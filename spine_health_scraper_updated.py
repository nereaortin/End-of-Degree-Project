import os
import re
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

KEYWORDS = [
    "exercise", "exercises", "routine", "routines", "warm up", "stretch", "stretches",
    "rehabilitation", "recovery", "treatment", "treatments", "therapy", "physical therapy",
    "management", "mobility", "relief", "improve", "motion", "strengthen", "strength",
    "home care", "treating", "healing", "recovering", "plan", "reduce", "back pain", "rehab"
]

def clean_condition_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# Load conditions
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = set()
for row in df["Related Conditions"].dropna():
    all_conditions.update([x.strip() for x in re.split(r"[/\n]+", row) if x.strip()])
all_conditions = list(all_conditions)

# Setup Selenium
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
# options.add_argument("--headless")  # Optional
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 12)

output_dir = "spinehealth_txt"
os.makedirs(output_dir, exist_ok=True)

for idx, condition in enumerate(all_conditions, 1):
    print(f"\n🔍 Searching: {condition} ({idx}/{len(all_conditions)})")
    try:
        driver.get("https://www.spine-health.com")

        # Accept cookie banner if it's the first load
        if idx == 1:
            try:
                consent_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fc-button.fc-cta-consent.fc-primary-button"))
                )
                consent_btn.click()
                print("✅ Cookie banner accepted.")
            except:
                print("ℹ️ No cookie banner found or already accepted.")

        # Open search
        search_icon = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#edit-submit")))
        search_icon.click()

        # Input search term
        search_input = wait.until(EC.presence_of_element_located((By.ID, "edit-keys")))
        search_input.clear()
        search_input.send_keys(condition)
        search_input.send_keys(Keys.ENTER)

        time.sleep(5)

        # Check for CAPTCHA
        try:
            captcha = driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            if captcha.is_displayed():
                print("🛑 CAPTCHA detected. Solve manually.")
                input("Press ENTER once CAPTCHA is solved...")
        except:
            pass

        # Rank search results
        results = driver.find_elements(By.CSS_SELECTOR, "div.gs-title a")
        best_match = None
        best_score = -1
        for r in results:
            title = r.text.lower()
            score = sum(1 for kw in KEYWORDS if kw in title)
            if condition.lower() in title:
                score += 5
            if score > best_score:
                best_match = r
                best_score = score

        if not best_match:
            print("❌ No relevant result found.")
            continue

        href = best_match.get_attribute("href")
        driver.get(href)
        print(f"🔗 Opening: {href}")
        time.sleep(4)

        # Close ad popup
        try:
            close_btn = driver.find_element(By.ID, "dismiss-button")
            if close_btn.is_displayed():
                close_btn.click()
                print("✅ Closed ad popup.")
        except:
            pass

        # Parse and extract clean text
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for tag in soup(["script", "style", "img", "video", "iframe", "header", "footer", "nav"]):
            tag.decompose()

        main = soup.find("div", class_="main-content")
        text = main.get_text(separator="\n", strip=True) if main else soup.get_text()

        # Save as .txt
        filename = clean_condition_name(condition) + ".txt"
        with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ Saved: {filename}")
        time.sleep(random.uniform(3.5, 6))

    except Exception as e:
        print(f"❌ Error with '{condition}': {e}")

driver.quit()
print("\n🏁 All done! Files saved in 'spinehealth_txt'")
