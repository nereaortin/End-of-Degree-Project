import re
import time
import os
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
    """
    Makes a file-friendly string for saving HTML (removes slashes, question marks, etc.).
    """
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# 1) Read CSV data from 'exercises.csv'
df = pd.read_csv("exercises.csv", encoding="utf-8")  

all_conditions = []
for row in df["Related Conditions"].dropna():
    # Split on slashes or newlines
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)

# Remove duplicates
all_conditions = list(set(all_conditions))

# 2) Setup Selenium
options = Options()
# options.add_argument("--headless") 
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 15)

base_url = "https://www.nhs.uk"

# Folder to store the final pages 
os.makedirs("nhs_html_pages", exist_ok=True)

for condition in all_conditions:
    print(f"\n[INFO] Searching for condition: '{condition}'")

    try:
        # 3) Go to the NHS homepage
        driver.get(base_url)
        time.sleep(2)

        # 3a) Accept cookie banner
        try:
            cookie_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept all cookies')]"))
            )
            cookie_btn.click()
            print("[INFO] Cookie banner accepted.")
            time.sleep(1)
        except:
            print("[INFO] No cookie banner found or not clickable.")

        # 4) Find the search box (id="search-field"), type condition, press Enter
        search_box = wait.until(EC.presence_of_element_located((By.ID, "search-field")))
        search_box.clear()
        search_box.send_keys(condition)
        search_box.send_keys(Keys.ENTER)

        # 5) Wait for the new results structure (ul.nhsuk-list)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.nhsuk-list")))

        # 6) Grab the actual anchors for each result
        result_links = driver.find_elements(
            By.CSS_SELECTOR,
            "ul.nhsuk-list li.nhsuk-list-item--border h2.nhsuk-heading-xs a"
        )
        if not result_links:
            print(f"[WARNING] No search results found for '{condition}'. Skipping.")
            continue

        # 7) Click the first link
        first_link = result_links[0]
        first_link_href = first_link.get_attribute("href")
        print(f"[INFO] Opening first result: {first_link_href}")
        first_link.click()

        # 8) Wait for final page to load, then save HTML
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        time.sleep(2)  
        page_html = driver.page_source

        safe_name = clean_condition_name(condition)
        file_path = os.path.join("nhs_html_pages", f"{safe_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"[INFO] Saved HTML to '{file_path}'")

    except Exception as e:
        print(f"[ERROR] Failed to process '{condition}': {e}")

driver.quit()
print("\n[INFO] All done! Check the 'nhs_html_pages' folder for saved pages.")
