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
    """
    Makes a file-friendly string (no slashes, question marks, etc.).
    """
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# 1) Read CSV data (exercises.csv)
df = pd.read_csv("exercises.csv", encoding="utf-8")

all_conditions = []
for row in df["Related Conditions"].dropna():
    # Split on slashes or newlines
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)

# Remove duplicates
all_conditions = list(set(all_conditions))

# 2) Setup Selenium
options = Options()
# Uncomment if you want headless:
# options.add_argument("--headless")

options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors=yes")
options.add_argument(
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/98.0.4758.102 Safari/537.36'
)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 30)

# 3) The HSS Conditions search page
base_url = "https://www.hss.edu/conditions.asp"

# Create a folder to store saved HTML pages
os.makedirs("hss_html_pages", exist_ok=True)

for condition in all_conditions:
    print(f"\n[INFO] Searching for condition: '{condition}'")

    try:
        # 4) Go to the HSS conditions page
        driver.get(base_url)
        time.sleep(2)

        # 5) Find the search box: <input class="st-default-search-input" placeholder="Search Conditions and Treatments">
        search_box = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "input.st-default-search-input[placeholder='Search Conditions and Treatments']"
            ))
        )
        search_box.clear()
        search_box.send_keys(condition)
        time.sleep(1)

        # 6) Press Enter to trigger the search (instead of clicking magnifying glass)
        search_box.send_keys(Keys.ENTER)

        # 7) Wait for the search results container: div.searchResults
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "st-ui-result")))


        # 8) Grab the first anchor for the search result
        #    Typically: <a class="st-ui-result st-ui-image __swiftype_result" href="...">
        
        anchor = driver.find_element(By.CSS_SELECTOR, "#centercolumn > div > div > div > div > div > div.st-ui-container-primary_content.st-position-container > div.st-ui-injected-content.st-search-results > div > a:nth-child(1)")
        if not anchor:
            print(f"[WARNING] No search results found for '{condition}'. Skipping.")
            continue

        #first_anchor = anchors[0]
        href = anchor.get_attribute("href")
        print(f"[INFO] Found first result. HREF => {href}")

        # 9) Attempt to click using normal click -> JS click -> direct navigate
        driver.execute_script("arguments[0].scrollIntoView(true);", anchor)
        time.sleep(1)

        clicked = False
        try:
            anchor.click()
            print("[INFO] Normal click succeeded.")
            clicked = True
        except Exception as e_click:
            print(f"[INFO] Normal click failed: {e_click}. Trying JS click.")
            try:
                driver.execute_script("arguments[0].click();", anchor)
                print("[INFO] JS click succeeded.")
                clicked = True
            except Exception as e_js:
                print(f"[INFO] JS click also failed: {e_js}")

        # If both click attempts failed, fallback to driver.get(href)
        if not clicked and href:
            print("[INFO] Navigating directly to href.")
            driver.get(href)
        elif not clicked:
            print(f"[ERROR] No valid href or click success. Skipping '{condition}'.")
            continue

        # 10) Wait for final page to load. Typically, it has <h1>...
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        time.sleep(2)

        # 11) Save HTML of the final page
        page_html = driver.page_source
        safe_name = clean_condition_name(condition)
        file_path = os.path.join("hss_html_pages", f"{safe_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_html)

        print(f"[INFO] Saved HTML to '{file_path}'")

    except Exception as e:
        print(f"[ERROR] Failed to process '{condition}': {e}")

    # 12) Optional pause between queries
    time.sleep(5)

driver.quit()
print("\n[INFO] All done! Check the 'hss_html_pages' folder for your saved pages.")
