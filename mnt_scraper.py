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

# Load CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)
all_conditions = list(set(all_conditions))

# Setup Selenium
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 12)

# Output folder
output_folder = "mnt_html_pages"
os.makedirs(output_folder, exist_ok=True)

for condition in all_conditions:
    print(f"\n[INFO] Searching: '{condition}'")
    try:
        driver.get("https://www.medicalnewstoday.com/")

        # Handle GDPR popup first
        try:
            gdpr_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'ACCEPT AND CONTINUE TO SITE')]"))
            )
            gdpr_button.click()
            print("[INFO] GDPR banner accepted.")
        except:
            print("[INFO] No GDPR banner found.")

        # Search workflow
        search_icon = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Open search']")))
        search_icon.click()
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Search']")))
        search_box.send_keys(condition)
        search_box.send_keys(Keys.ENTER)

        # Click first result
        first_result = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.css-1i0edl6 a")))
        driver.execute_script("arguments[0].click();", first_result)

        # Handle potential newsletter popup
        try:
            popup_close = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Close']")))
            popup_close.click()
            print("[INFO] Newsletter popup closed.")
        except:
            print("[INFO] No popup found.")

        # Save the final article page
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        time.sleep(2)
        page_html = driver.page_source
        safe_name = clean_condition_name(condition)
        file_path = os.path.join(output_folder, f"{safe_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"[INFO] Saved HTML to '{file_path}'")

    except Exception as e:
        print(f"[ERROR] Issue with '{condition}': {e}")

driver.quit()
print("\n✅ Done! Check your folder for the saved HTML files.")
