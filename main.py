import os
import re
import random
import unicodedata

from playwright.sync_api import sync_playwright


PROXIES = [
    None,
]
LOOP_CATEGORIES = False
html_files_directory='./html_pages'
os.makedirs(html_files_directory, exist_ok=True)

def make_filename_friendly(filename):
    filename = filename.lower()

    prefixes = ["http://", "https://", "www."]
    for prefix in prefixes:
        if filename.startswith(prefix):
            filename = filename[len(prefix):]

    filename = filename.replace(" ", "_")

    filename = re.sub(r"[?!;:/()]+", "", filename)

    filename = (
        unicodedata.normalize("NFD", filename).encode("ascii", "ignore").decode("utf-8")
    )

    max_length = 255
    if len(filename) > max_length:
        filename = filename[-max_length:]

    return filename

def save_page_content(page, directory_path):
    page_content = page.content()

    current_active_paginated_btn = page.query_selector('.v-pagination__item.v-pagination__item--active')
    
    if current_active_paginated_btn:
        match = re.search(r'\d+', current_active_paginated_btn.get_attribute('aria-label'))
        
        if match:
            extracted_number = int(match.group())
            file_name = f"{extracted_number}.html"
            page_content = page.content()

            file_path = os.path.join(directory_path, file_name)
                
            if os.path.exists(file_path):
                print('Page Alrady Scraped')
            else:
                scroll_through_each_row(page)

                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(page_content)
        else:
            print("No number found in the string.")

def create_scrape_complete_file(file_directory):
    file_path = os.path.join(file_directory, 'scrape_complete.txt')
    
    with open(file_path, 'w') as file:
        pass

def scroll_through_each_row(page):
    # Go through each row to ensure image loads and click more button in price column
    table_selector = 'div.product-table > div.table-area > table'
    rows_selector = f'{table_selector} > tbody > tr'

    rows_selector_list = page.query_selector_all(rows_selector)

    # Get the total number of rows in the table
    total_rows = len(rows_selector_list)

    
    for row_index in range(total_rows):
    #   Scroll to the row
        nth_child_selector = f'{rows_selector}:nth-child({row_index + 1})'
        more_price_btn = page.query_selector(f'{nth_child_selector} > ' +
                                                'td.column-price div > ' + 
                                                'div > button > span.v-btn__content')        
        page.eval_on_selector(
            nth_child_selector,
            'element => element.scrollIntoView()'
        )
        
        if more_price_btn:
            more_price_btn.click()
        else:
            page.wait_for_timeout(500)

    # price_row_more_btn = page.query_selector('fixed-column column-price')

def navigate_to_save_pages(page, directory_path = html_files_directory):
    dropdown_selector = '.v-select__slot'
        
    if dropdown_selector:
        page.click(dropdown_selector)

        drop_down_100 = page.query_selector('.v-list-item > div.v-list-item__content > div.v-list-item__title:text("100")')
        
        if drop_down_100:
            drop_down_100.click()
            page.wait_for_timeout(2000)

            navigation = page.query_selector('[aria-label = "Pagination Navigation"]')
            if navigation:
                next_page_btn = page.query_selector('.v-pagination__navigation[aria-label = "Next page"]')
                next_page_btn_disabled = "v-pagination__navigation--disabled" 

                while(next_page_btn_disabled not in next_page_btn.get_attribute('class')):
                    save_page_content(page, directory_path)

                    next_page_btn.click()
                    page.wait_for_timeout(2000)

                save_page_content(page, directory_path)
                create_scrape_complete_file(directory_path)
            else:
                print('Navigation not found')
        else:
            print('Per page item drop down does not has 100 value')
    else:
        print('drop down selector not found')

is_scraped = lambda path: os.path.exists(os.path.join(path, 'scrape_complete.txt'))
def scrape_page(url, proxy=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, wait_until="load")

        if LOOP_CATEGORIES is False:                     
            print("Page already scraped!") if is_scraped(html_files_directory) else  navigate_to_save_pages(page)
        elif LOOP_CATEGORIES is True:
            manufacturer_selector = page.query_selector_all('.flex-grow-0.col > ' + 
                                                        'div.pb-2.font-Bold:text("Manufacturer") + ' +
                                                        'div.box > select.param-selector > option')
            apply_btn = page.query_selector('button > span.v-btn__content:text("Apply")')

            if manufacturer_selector:
                manufacturers_list = {m.inner_text(): make_filename_friendly(m.inner_text()) for m in manufacturer_selector}
                
                for manufacturer in manufacturer_selector:
                    directory_path = f"{html_files_directory}/{manufacturers_list[manufacturer.inner_text()]}"
                    os.makedirs(directory_path, exist_ok=True)

                    if is_scraped(directory_path):
                        print("Page already scraped!")
                    else:
                        manufacturer.click()
                        page.wait_for_timeout(500)
                        apply_btn.click()
                        page.wait_for_timeout(2000)
                        navigate_to_save_pages(page, directory_path)
                        page.wait_for_timeout(1000)
        browser.close()

proxy = random.choice(PROXIES)


scrape_page(
    "https://www.lcsc.com/products/Microcontroller-Units-MCUs-MPUs-SOCs_11329.html"
)