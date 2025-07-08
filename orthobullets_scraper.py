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

# Read conditions
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)
all_conditions = list(set(all_conditions))

# Setup browser
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 15)
os.makedirs("orthobullets_html_pages", exist_ok=True)

for condition in all_conditions:
    print(f"\n[INFO] Searching for condition: '{condition}'")
    try:
        driver.get("https://www.orthobullets.com/")
        time.sleep(2)

        # Click & type in search box
        search_box = wait.until(EC.element_to_be_clickable((By.ID, "searchbox")))
        search_box.click()
        search_box.clear()
        search_box.send_keys(condition)
        search_box.send_keys(Keys.RETURN)  # Actually submit search with Enter

        # Handle quick search overlay if it appears
        try:
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "main-content-overlay--shown")))
        except:
            pass

        # Wait for results & click first result
        first_result = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.dashboard-item__main-info")))
        first_result.click()

        # Save page
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        time.sleep(1)
        page_html = driver.page_source
        safe_name = clean_condition_name(condition)
        file_path = os.path.join("orthobullets_html_pages", f"{safe_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"[INFO] Saved HTML to '{file_path}'")

    except Exception as e:
        print(f"[ERROR] Failed to process '{condition}': {e}")

driver.quit()
print("\n[INFO] All done! Check the 'orthobullets_html_pages' folder for saved pages.")
