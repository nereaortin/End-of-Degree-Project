import os
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def clean_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# Load conditions from CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    items = re.split(r"[/\n]+", row)
    all_conditions.extend([i.strip() for i in items if i.strip()])
all_conditions = list(set(all_conditions))

# Selenium setup
options = Options()
# options.add_argument("--headless")  # Optional
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

BASE_URL = "https://www.verywellhealth.com/"
SAVE_DIR = "verywellhealth_html_pages"
os.makedirs(SAVE_DIR, exist_ok=True)

for i, condition in enumerate(all_conditions):
    print(f"\n🔍 Searching: {condition} ({i+1}/{len(all_conditions)})")
    try:
        driver.get(BASE_URL)

        # Accept cookie if appears
        try:
            cookie_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_btn.click()
            print("✅ Cookie consent accepted.")
        except:
            print("ℹ️ No cookie consent popup.")

        # Click search icon
        try:
            search_icon = wait.until(EC.element_to_be_clickable((By.ID, "header-search-button_1-0")))
            search_icon.click()
        except Exception as e:
            print(f"❌ Could not click search icon: {e}")
            continue

        # Enter condition in search input
        try:
            search_input = wait.until(EC.presence_of_element_located((By.ID, "search-input")))
            search_input.clear()
            search_input.send_keys(condition)

            search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-bright.btn-go")))
            search_button.click()
        except Exception as e:
            print(f"❌ Search input or button failed: {e}")
            continue

        # Wait and click the first result
        try:
            first_result = WebDriverWait(driver, 7).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.loc.featured-result a"))
            )
            href = first_result.get_attribute("href")
            driver.get(href)
            print(f"🔗 Navigated to: {href}")
        except Exception as e:
            print(f"❌ Failed to open first result: {e}")
            continue

        # Save HTML
        safe_name = clean_name(condition)
        html = driver.page_source
        with open(os.path.join(SAVE_DIR, f"{safe_name}.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print(f"💾 Saved HTML: {safe_name}.html")

        time.sleep(3)  # Light pause between requests

    except Exception as e:
        print(f"❌ Unexpected error with '{condition}': {e}")

driver.quit()
print("\n✅ Finished scraping Verywell Health.")
