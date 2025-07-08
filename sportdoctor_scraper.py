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

def clean_condition_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# Load conditions from CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    all_conditions.extend([c.strip() for c in re.split(r"[/\n]+", row) if c.strip()])
all_conditions = list(set(all_conditions))  # remove duplicates

# Output folder
output_folder = "sportdoctor_html_pages"
os.makedirs(output_folder, exist_ok=True)

# Configure Chrome (speed boost)
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--start-maximized")
options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2,
    "profile.managed_default_content_settings.fonts": 2,
})
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

# Base URL
base_url = "https://sportdoctorlondon.com/"

for i, condition in enumerate(all_conditions):
    print(f"\n[INFO] Searching for: {condition}")
    try:
        driver.get(base_url)

        # Accept cookie only on first load
        if i == 0:
            try:
                accept_btn = WebDriverWait(driver, 4).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.sc-knesRu.ePGZca.amc-focus-first"))
                )
                accept_btn.click()
                print("[INFO] Cookie banner accepted.")
            except:
                print("[INFO] No cookie banner appeared.")

        # Click the search icon
        search_icon = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "a.fusion-main-menu-icon.fusion-bar-highlight")))
        search_icon.click()

        # Type condition in search input
        search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']")))
        search_input.clear()
        search_input.send_keys(condition)

        # Click search button
        search_btn = driver.find_element(By.CSS_SELECTOR, "input.fusion-search-submit.searchsubmit")
        search_btn.click()

        # Click the first search result (FIXED SELECTOR)
        first_result = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "h2.blog-shortcode-post-title.entry-title a"))
        )
        article_url = first_result.get_attribute("href")
        print(f"[INFO] Opening article: {article_url}")
        driver.get(article_url)

        # Wait and save HTML
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        html = driver.page_source
        safe_name = clean_condition_name(condition)
        output_path = os.path.join(output_folder, f"{safe_name}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[✔] Saved: {output_path}")

    except Exception as e:
        print(f"[❌ ERROR] '{condition}': {e}")

driver.quit()
print("\n✅ All done! Check your 'sportdoctor_html_pages' folder.")
