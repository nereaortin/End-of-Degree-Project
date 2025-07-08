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

# Load your CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")  
all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)
all_conditions = list(set(all_conditions))

# Setup Selenium
options = Options()
# options.add_argument("--headless")  # Uncomment if you want headless mode
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 15)

base_url = "https://www.sciencedirect.com/#open-access"
os.makedirs("sciencedirect_html_pages", exist_ok=True)

for condition in all_conditions:
    print(f"\n[INFO] Searching: '{condition}'")

    try:
        driver.get(base_url)
        time.sleep(2)

        # Accept cookie banner (first one)
        try:
            cookie_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_btn.click()
            print("[INFO] Accepted first cookie banner.")
            time.sleep(1)
        except:
            print("[INFO] First cookie banner not found.")

        # Fill search box and click search
        search_box = wait.until(EC.presence_of_element_located((By.ID, "qs")))
        search_box.clear()
        search_box.send_keys(condition)
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        print("[INFO] Submitted search.")

        # Accept second cookie banner (appears after search)
        try:
            cookie_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_btn.click()
            print("[INFO] Accepted second cookie banner.")
            time.sleep(1)
        except:
            print("[INFO] Second cookie banner not found.")

        # Handle organization modal
        try:
            org_input_box = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "bdd-els-discovery-search"))
            )
            print("[INFO] Organization modal detected. Typing 'Medtronic'.")
            org_input_box.clear()
            org_input_box.send_keys("Medtronic")
            org_input_box.send_keys(Keys.ENTER)
            time.sleep(4)  # Adjust if needed
        except:
            try:
                close_btn = driver.find_element(By.ID, "bdd-els-close")
                close_btn.click()
                print("[INFO] Closed organization modal via X.")
            except:
                print("[INFO] Organization modal not found.")

        # Get first search result
        try:
            result_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.anchor.result-list-title-link")))
            href = result_link.get_attribute("href")
            print(f"[INFO] Clicking result: {href}")
            result_link.click()
        except:
            print(f"[WARNING] No results found for '{condition}'. Skipping.")
            continue

        # Save page content
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        time.sleep(2)
        page_html = driver.page_source
        safe_name = clean_condition_name(condition)
        file_path = os.path.join("sciencedirect_html_pages", f"{safe_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"[INFO] Saved HTML to '{file_path}'")

    except Exception as e:
        print(f"[ERROR] Issue processing '{condition}': {e}")

driver.quit()
print("\n[INFO] All done! Check the 'sciencedirect_html_pages' folder.")
