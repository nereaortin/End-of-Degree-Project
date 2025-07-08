import re
import time
import os
import random
import pandas as pd
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Function to clean condition names
def clean_condition_name(name: str) -> str:
    """Cleans condition names by removing text inside parentheses and text after hyphens."""
    name = re.sub(r"\(.*?\)", "", name)  # Remove text inside ()
    name = re.split(r" - ", name)[0]  # Keep only text before " - "
    return name.strip()  # Remove leading/trailing spaces

# Read CSV data from 'exercises_cleaned.csv'
df = pd.read_csv("exercises_cleaned.csv", encoding="utf-8")

# Extract & split related conditions into individual searches
all_conditions = []
for row in df["Cleaned Conditions"].dropna():
    conditions = row.split("\n")  # Split multiple conditions in a single row
    all_conditions.extend([clean_condition_name(cond) for cond in conditions if cond.strip()])

# Remove duplicates
all_conditions = list(set(all_conditions))

# Setup Selenium + Stealth
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")  # Helps avoid detection
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/110.0.5481.77 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

# Enable Headless mode for speed (Optional)
# options.add_argument("--headless")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# Apply selenium-stealth
stealth(
    driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

wait = WebDriverWait(driver, 10)  # Reduced wait time to speed up execution
base_url = "https://www.healthline.com"
os.makedirs("healthline_html_pages", exist_ok=True)

for condition in all_conditions:
    print(f"\n[INFO] Searching for condition: '{condition}'")

    time.sleep(random.uniform(1, 3))  # Reduce wait times

    try:
        # 1) Open Healthline homepage
        driver.get(base_url)

        # 2) Accept cookie banner if present
        try:
            cookie_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.css-whh5e5'))
            )
            cookie_btn.click()
            print("[INFO] Accepted cookies.")
        except:
            print("[INFO] No cookie banner found or already accepted.")

        # 3) Click the search button to open the search bar
        try:
            search_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="nav-search-button"]'))
            )
            search_button.click()
            print("[INFO] Clicked on search button.")
        except:
            print("[ERROR] Could not find or click the search button.")
            continue

        # 4) Find the search input field, type condition, press Enter
        try:
            search_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input.autocomplete[name="q1"]'))
            )
            search_input.clear()
            search_input.send_keys(condition)
            search_input.send_keys(Keys.ENTER)
            print(f"[INFO] Searched for '{condition}'")
        except:
            print("[ERROR] Search input field not found.")
            continue

        # 5) Open the first search result
        try:
            first_result = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.css-17zb9f8'))
            )
            first_result_href = first_result.get_attribute("href")
            print(f"[INFO] Opening first result: {first_result_href}")
            driver.get(first_result_href)
        except:
            print(f"[WARNING] No search results found for '{condition}'. Skipping.")
            continue

        # 6) Close any pop-up windows
        try:
            popup_buttons = [
                'button[data-testid="modal-close-button"]',  # Common pop-up close button
                'button.icon-hl-close.window-close-button.selector.css-1dt8f8e'  # Another close button selector
            ]
            for popup_selector in popup_buttons:
                try:
                    popup_close_button = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, popup_selector))
                    )
                    popup_close_button.click()
                    print("[INFO] Closed popup ad.")
                    break  # Stop checking if one popup was successfully closed
                except:
                    continue
        except:
            print("[INFO] No popups found.")

        # 7) Save HTML page
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))  # Wait for main content
        page_html = driver.page_source

        safe_name = clean_condition_name(condition)
        file_path = os.path.join("healthline_html_pages", f"{safe_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"[INFO] Saved HTML to '{file_path}'")

    except Exception as e:
        print(f"[ERROR] Failed to process '{condition}': {e}")

driver.quit()
print("\n[INFO] All done! Check the 'healthline_html_pages' folder for saved pages.")
