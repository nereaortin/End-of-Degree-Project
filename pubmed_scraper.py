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

# Read conditions from CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)
all_conditions = list(set(all_conditions))

# Setup Selenium
options = Options()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

# Output folder
os.makedirs("pubmed_html_pages", exist_ok=True)

base_url = "https://pubmed.ncbi.nlm.nih.gov/"

for condition in all_conditions:
    print(f"\n[INFO] Searching for condition: '{condition}'")
    try:
        driver.get(base_url)
        
        # Fill the search box
        search_box = wait.until(EC.presence_of_element_located((By.ID, "id_term")))
        search_box.clear()
        search_box.send_keys(condition)
        
        # Submit the search
        search_button = driver.find_element(By.CSS_SELECTOR, "button.search-btn")
        search_button.click()

        # Click the first result
        first_result = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.docsum-title")))
        first_result.click()
        print("[INFO] Opened first result.")

        time.sleep(2)

        # Check for 'free full text' or 'free pdf'
        try:
            free_link = driver.find_element(By.CSS_SELECTOR, "a.link-item[href*='fulltext'], a.link-item[href*='pmc']")
            href = free_link.get_attribute("href")
            print(f"[INFO] Found free full text link: {href}")
            driver.get(href)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except:
            print("[INFO] No free full text link found, saving main article page.")

        # Save page as HTML
        time.sleep(2)
        page_html = driver.page_source
        safe_name = clean_condition_name(condition)
        file_path = os.path.join("pubmed_html_pages", f"{safe_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"[INFO] Saved HTML to '{file_path}'")

    except Exception as e:
        print(f"[ERROR] Failed to process '{condition}': {e}")

driver.quit()
print("\n✅ All done! Check the 'pubmed_html_pages' folder for saved pages.")
