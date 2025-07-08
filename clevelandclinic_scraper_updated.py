import time
import os
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# -------------------------
# Step 1: Read CSV and Extract Conditions
# -------------------------
df = pd.read_csv("exercises.csv", encoding="utf-8")

all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)

all_conditions = list(set(all_conditions))
print(f"[INFO] Loaded {len(all_conditions)} unique conditions from CSV.")

# -------------------------
# Step 2: Setup Selenium
# -------------------------
options = Options()
# options.add_argument("--headless")  # Headless optional
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(), options=options)
wait = WebDriverWait(driver, 10)

base_url = "https://my.clevelandclinic.org/health"

# Create output folder
os.makedirs("clevelandclinic_html_pages", exist_ok=True)

# -------------------------
# Step 3: Process Each Condition
# -------------------------
driver.get(base_url)

for condition in all_conditions:
    try:
        print(f"[INFO] Searching: '{condition}'")
        wait.until(EC.presence_of_element_located((By.ID, "search-input")))

        search_input = driver.find_element(By.ID, "search-input")
        search_input.clear()
        search_input.send_keys(condition)

        search_button = driver.find_element(By.CLASS_NAME, "health-search__search-button")
        search_button.click()

        try:
            result_count_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.info-bar-count__number")))
            if "0 Results" in result_count_element.text:
                print(f"[SKIP] No results for '{condition}'")
                driver.get(base_url)
                continue

            # Open first result
            first_result = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.index-list__title h4")))
            driver.execute_script("arguments[0].click();", first_result)
            time.sleep(2)

            # Clean the content
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Remove unnecessary elements
            for selector in [
                "header", "footer", "script", "noscript", "aside", "img", "video",
                "div.article-sidebar",
                "div[data-identity='inline-cta-panel']",
                "div.flex-row.gap-x-rem32px",
                "section.py-rem32px.border-y.border-gray-400.mt-rem32px",
                "section.contact-ribbon"
            ]:
                for el in soup.select(selector):
                    el.decompose()

            # Get the main content
            main = soup.select_one("div[data-identity='main-article-content']")
            if main:
                cleaned_html = f"<html><head><meta charset='utf-8'><title>{condition}</title></head><body>{str(main)}</body></html>"
            else:
                cleaned_html = "<html><body><p>No content found.</p></body></html>"

            # Save
            safe_name = re.sub(r'[\\/*?:"<>|]', "_", condition)
            with open(f"clevelandclinic_html_pages/{safe_name}.html", "w", encoding="utf-8") as f:
                f.write(cleaned_html)
            print(f"[✅ SAVED] {safe_name}.html")

        except Exception as e:
            print(f"[❌ ERROR] While processing result for '{condition}': {e}")

        driver.get(base_url)
        time.sleep(1)

    except Exception as e:
        print(f"[❌ ERROR] Condition '{condition}': {e}")
        driver.get(base_url)
        time.sleep(1)

driver.quit()
print("[✅ DONE] All conditions processed and cleaned.")
