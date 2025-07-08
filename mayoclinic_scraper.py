import re
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
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# 1) Read CSV data from 'exercises.csv'
df = pd.read_csv("exercises.csv", encoding="utf-8")  

all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)
all_conditions = list(set(all_conditions))

# 2) Setup Selenium
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--start-maximized")
# Uncomment below to run headless
# options.add_argument("--headless=new")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 7)

base_url = "https://www.mayoclinic.org"

os.makedirs("mayo_html_pages", exist_ok=True)

for condition in all_conditions:
    print(f"\n[INFO] Searching for condition: '{condition}'")

    try:
        driver.get(base_url)

        # Click the search button (top right)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.cmp-search-button button"))).click()

        # Input search term
        search_box = wait.until(EC.presence_of_element_located((By.ID, "search-input-globalsearch-773693aac3")))
        search_box.clear()
        search_box.send_keys(condition)

        # Submit search
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.search-button.sc-mc-search[type='submit']"))).click()

        # Click first result
        first_result = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.azsearchlink")))
        result_url = first_result.get_attribute("href")
        print(f"[INFO] Clicking first result: {result_url}")
        first_result.click()

        # Wait for page to load and save HTML
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        page_html = driver.page_source

        safe_name = clean_condition_name(condition)
        file_path = os.path.join("mayo_html_pages", f"{safe_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"[INFO] Saved HTML to '{file_path}'")

    except Exception as e:
        print(f"[ERROR] Failed to process '{condition}': {e}")

driver.quit()
print("\n✅ All done! Check the 'mayo_html_pages' folder for saved pages.")
