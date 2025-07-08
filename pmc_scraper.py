import os
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def clean_condition_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# Load CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    all_conditions.extend([c.strip() for c in splitted if c.strip()])
all_conditions = list(set(all_conditions))

# Faster Selenium options
options = Options()
prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2,
    "profile.managed_default_content_settings.fonts": 2
}
options.add_experimental_option("prefs", prefs)
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-extensions")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

os.makedirs("pmc_html_pages", exist_ok=True)
base_url = "https://pmc.ncbi.nlm.nih.gov/"

for condition in all_conditions:
    print(f"\n[INFO] Searching for: '{condition}'")
    try:
        driver.get(base_url)

        # Enter search
        search_box = wait.until(EC.presence_of_element_located((By.ID, "pmc-search")))
        search_box.clear()
        search_box.send_keys(condition)

        # Submit search
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-ga-label='PMC_search_button']")))
        driver.execute_script("arguments[0].click();", submit_button)
        print("[INFO] Search submitted.")

        # First result
        first_result = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.title a.view")))
        first_result.click()
        print("[INFO] Clicked on first result.")

        # Save page
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        html = driver.page_source
        file_path = os.path.join("pmc_html_pages", f"{clean_condition_name(condition)}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[INFO] Saved HTML to '{file_path}'")

    except Exception as e:
        print(f"[ERROR] Failed for '{condition}': {e}")

driver.quit()
print("\n⚡ Done faster! Check 'pmc_html_pages' folder.")
