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

# ---------- Utility ----------
def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# ---------- Constants ----------
BASE_URL = "https://www.sportsinjuryclinic.net"
OUTPUT_DIR = "sportsinjury_html_pages"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------- Load conditions ----------
df = pd.read_csv("exercises.csv", encoding="utf-8")
conditions = []
for row in df["Related Conditions"].dropna():
    parts = re.split(r"[/\n]+", row)
    conditions.extend([p.strip() for p in parts if p.strip()])
conditions = list(set(conditions))  # Remove duplicates

# ---------- Set up Selenium ----------
options = Options()
options.add_argument("--start-maximized")  # See browser actions
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

# ---------- Loop ----------
for condition in conditions:
    print(f"\n🔍 Searching: {condition}")
    try:
        driver.get(BASE_URL)

        # Accept cookie if needed
        try:
            cookie_btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fc-cta-consent"))
            )
            cookie_btn.click()
            print("✅ Cookie accepted")
        except:
            print("ℹ️ Cookie already handled")

        # Click the search icon using full class
        search_icon = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "a.slide-search.astra-search-icon")
        ))
        search_icon.click()

        # Wait for search field, enter query and submit
        search_input = wait.until(EC.visibility_of_element_located((By.ID, "search-field")))
        search_input.clear()
        search_input.send_keys(condition)
        search_input.send_keys(Keys.ENTER)

        # Wait and click first result
        result = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "p.ast-blog-single-element.ast-read-more-container.read-more > a")
        ))
        link = result.get_attribute("href")
        print(f"➡️ Clicking result: {link}")
        driver.get(link)

        # Save HTML
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        html = driver.page_source
        filename = clean_filename(condition) + ".html"
        with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Saved: {filename}")

    except Exception as e:
        print(f"❌ Error for '{condition}': {e}")

driver.quit()
print("\n🏁 Done scraping.")
