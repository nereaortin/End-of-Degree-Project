import os
import re
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def clean_condition_name(name: str) -> str:
    """Creates a file-friendly string for saving HTML files."""
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# 1) Read CSV data
df = pd.read_csv("exercises.csv", encoding="utf-8")  

# Extract all conditions
all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)

# Remove duplicates
all_conditions = list(set(all_conditions))

# 2) Setup Selenium
options = Options()
options.add_argument("--headless")  
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")  
options.add_argument("--ignore-certificate-errors")  
options.add_argument("--incognito")  
options.add_argument("--disable-dev-shm-usage")  
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.77 Safari/537.36")  

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 15)

# Folder to store HTML pages
os.makedirs("physiopedia_html_pages", exist_ok=True)

base_url = "https://www.physio-pedia.com/home/"

for condition in all_conditions:
    print(f"\n[INFO] Searching for condition: '{condition}'")

    retry_count = 0
    while retry_count < 3:  
        try:
            # 3) Open Physio-Pedia Homepage
            driver.get(base_url)
            time.sleep(random.uniform(2, 4))  

            # 3a) Accept cookie banner if present
            try:
                cookie_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
                )
                cookie_btn.click()
                print("[INFO] Cookie banner accepted.")
                time.sleep(1)
            except:
                print("[INFO] No cookie banner found.")

            # 4) Ensure search box is visible
            search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.pp-home-search.st-default-search-input")))
            
            # Scroll into view and click using JavaScript to bypass overlays
            driver.execute_script("arguments[0].scrollIntoView();", search_box)
            driver.execute_script("arguments[0].click();", search_box)
            time.sleep(1)  

            # 5) Type the Search Query
            search_box.clear()
            search_box.send_keys(condition)
            search_box.send_keys(Keys.ENTER)

            # 6) Wait for Search Results
            time.sleep(random.uniform(3, 6))  
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.st-ui-content.st-search-results")))

            # 7) Click First Search Result
            result_links = driver.find_elements(By.CSS_SELECTOR, "a.st-ui-result")
            if not result_links:
                print(f"[WARNING] No search results found for '{condition}'. Skipping.")
                break  

            first_link = result_links[0]
            first_link_href = first_link.get_attribute("href")
            print(f"[INFO] Opening first result: {first_link_href}")
            driver.get(first_link_href)

            # 8) Wait for Page to Load
            wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
            time.sleep(2)  

            # 9) Save HTML
            page_html = driver.page_source
            safe_name = clean_condition_name(condition)
            file_path = os.path.join("physiopedia_html_pages", f"{safe_name}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(page_html)
            print(f"[INFO] Saved HTML to '{file_path}'")

            time.sleep(random.uniform(5, 10))
            break  

        except Exception as e:
            retry_count += 1
            print(f"[ERROR] Failed to process '{condition}', retry {retry_count}/3: {e}")
            time.sleep(random.uniform(10, 20))  

    if retry_count == 3:
        print(f"[CRITICAL] Skipping '{condition}' after 3 failed attempts.")

driver.quit()
print("\n[INFO] All done! Check the 'physiopedia_html_pages' folder for saved pages.")
