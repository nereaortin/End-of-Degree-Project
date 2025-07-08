import os
import re
import time
import random
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

# Load conditions
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    items = re.split(r"[/\n]+", row)
    all_conditions.extend([i.strip() for i in items if i.strip()])
all_conditions = list(set(all_conditions))

# Setup Selenium
options = Options()
# options.add_argument("--headless")  # Optional if you want to hide the browser
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

base_url = "https://www.spine-health.com"
os.makedirs("spinehealth_html_pages", exist_ok=True)

for idx, condition in enumerate(all_conditions, 1):
    print(f"\n🔍 Searching: {condition} ({idx}/{len(all_conditions)})")
    try:
        driver.get(base_url)

        # Accept cookie banner
        try:
            consent_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fc-button.fc-cta-consent.fc-primary-button"))
            )
            consent_btn.click()
            print("✅ Cookie consent accepted.")
        except:
            print("ℹ️ No cookie banner or already accepted.")

        # Click search icon
        try:
            search_icon = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#edit-submit")))
            search_icon.click()
        except Exception as e:
            print(f"❌ Couldn't click search icon: {e}")
            continue

        # Enter condition in search input
        try:
            search_input = wait.until(EC.presence_of_element_located((By.ID, "edit-keys")))
            search_input.clear()
            search_input.send_keys(condition)
            search_input.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"❌ Search input failed: {e}")
            continue

        # Wait for results to appear
        time.sleep(5)

        # Detect CAPTCHA only if it's visible
        try:
            captcha_frame = driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            if captcha_frame.is_displayed():
                print("⚠️ CAPTCHA detected. Please solve it manually.")
                input("🔓 After solving the CAPTCHA, press ENTER to continue...")
        except:
            pass  # CAPTCHA not present or not visible

        # Click on first result
        try:
            first_result = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.gs-title a"))
            )
            href = first_result.get_attribute("href")
            driver.get(href)
            print(f"🔗 Navigated to: {href}")
        except Exception as e:
            print(f"❌ Couldn't open result: {e}")
            continue

        # Accept second cookie popup if it shows again
        try:
            second_cookie = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fc-button.fc-cta-consent.fc-primary-button"))
            )
            second_cookie.click()
            print("✅ Second cookie accepted.")
        except:
            pass

        # Save HTML
        safe_name = clean_condition_name(condition)
        html = driver.page_source
        with open(os.path.join("spinehealth_html_pages", f"{safe_name}.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print(f"💾 Saved HTML: spinehealth_html_pages\\{safe_name}.html")

        time.sleep(random.uniform(4, 6))  # Polite pause

    except Exception as e:
        print(f"❌ Error processing '{condition}': {e}")

driver.quit()
print("\n✅ Scraping complete!")
