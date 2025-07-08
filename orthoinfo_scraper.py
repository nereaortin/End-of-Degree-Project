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
    return re.sub(r'[\\/*?:"<>|]', '_', name)

df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)
all_conditions = list(set(all_conditions))

options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 8)

os.makedirs("orthoinfo_html_pages", exist_ok=True)
base_url = "https://orthoinfo.aaos.org/"

driver.get(base_url)
time.sleep(1)

# Accept cookies only once
try:
    cookie_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All Cookies')]"))
    )
    cookie_btn.click()
    print("[INFO] Accepted cookies.")
except:
    print("[INFO] Cookie banner not present or already accepted.")

for condition in all_conditions:
    print(f"\n[INFO] Searching for condition: '{condition}'")

    try:
        # Instead of reopening the homepage every time, clear search box
        search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']")))
        search_box.clear()
        search_box.send_keys(condition)
        search_box.send_keys(Keys.ENTER)

        first_result = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "a.article-list-item.search-listing-item")))
        href = first_result.get_attribute("href")
        print(f"[INFO] Clicking valid result: {href}")
        driver.get(href)

        time.sleep(1.5)  # shortened wait for page load
        page_html = driver.page_source
        print(f"[INFO] HTML size: {len(page_html)} chars.")

        safe_name = clean_condition_name(condition)
        file_path = os.path.join("orthoinfo_html_pages", f"{safe_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"[INFO] ✅ Saved to '{file_path}'")

        driver.back()  # Go back to search results instead of full reload
        time.sleep(0.5)

    except Exception as e:
        print(f"[ERROR] Failed to process '{condition}': {e}")
        driver.get(base_url)  # Reset if anything fails

driver.quit()
print("\n[INFO] 🚀 All done! Faster scraping complete.")
