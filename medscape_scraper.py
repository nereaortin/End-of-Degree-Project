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
from credentials import MEDSCAPE_EMAIL, MEDSCAPE_PASSWORD


def clean_condition_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)


def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless=new")  # headless for speed
    # Disable loading of images and stylesheets
    chrome_options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2
    })
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver, WebDriverWait(driver, 10)


def handle_login_popup(driver, wait):
    try:
        iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        driver.switch_to.frame(iframe)
        print("[INFO] Switched to login iframe.")

        # Enter email
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "regEmail")))
        email_input.click()
        email_input.send_keys(MEDSCAPE_EMAIL)

        # Submit email
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.mdscp-button--submit")))
        submit_button.click()

        # Enter password
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_input.send_keys(MEDSCAPE_PASSWORD)

        # Final login submit
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.mdscp-button--submit")))
        login_button.click()

        driver.switch_to.default_content()
        print("[INFO] Login completed.")
        time.sleep(2)

    except Exception as e:
        print(f"[WARNING] Failed to handle login form: {e}")
        driver.switch_to.default_content()


# Load CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)
all_conditions = list(set(all_conditions))

# Run browser
driver, wait = init_driver()
base_url = "https://www.medscape.com/"
os.makedirs("medscape_html_pages", exist_ok=True)

for i, condition in enumerate(all_conditions):
    print(f"\n[INFO] Searching for: '{condition}'")
    try:
        driver.get(base_url)
        time.sleep(1)

        # Accept cookie banner
        try:
            cookie_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'I Accept')]"))
            )
            cookie_btn.click()
            print("[INFO] Cookie banner accepted.")
        except:
            pass

        # Perform search
        search_box = wait.until(EC.presence_of_element_located((By.ID, "search-input")))
        search_box.clear()
        search_box.send_keys(condition)
        search_box.send_keys(Keys.ENTER)

        # Click first result
        result_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "p.searchResultTitle a"))
        )
        result_link.click()
        time.sleep(2)

        # Detect and handle login/register
        if "Log in or register for free" in driver.page_source:
            print("[INFO] Login/register overlay detected.")
            handle_login_popup(driver, wait)

        # Save content
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        html_content = driver.page_source
        file_name = clean_condition_name(condition) + ".html"
        path = os.path.join("medscape_html_pages", file_name)

        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"[INFO] Saved: '{file_name}'")

        if (i + 1) % 15 == 0:
            driver.quit()
            print("[INFO] Restarting browser to clear memory...")
            driver, wait = init_driver()

    except Exception as e:
        print(f"[ERROR] Failed for '{condition}': {e}")

driver.quit()
print("\n✅ Done! Check your 'medscape_html_pages' folder.")
