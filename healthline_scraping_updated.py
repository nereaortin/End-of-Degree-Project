import os
import re
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
 
# Clean filenames
def clean_condition_name(name: str) -> str:
    name = re.sub(r"[\\/*?\"<>|:]", "_", name)
    return name.strip()
 
# Load CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
if "Related Conditions" not in df.columns:
    raise KeyError("Column 'Related Conditions' not found in CSV.")
 
all_conditions = []
for row in df["Related Conditions"].dropna():
    items = re.split(r"[/\n]+", row)
    all_conditions.extend([item.strip() for item in items if item.strip()])
all_conditions = list(set(all_conditions))  # Unique conditions
 
# Setup browser
options = Options()
# options.add_argument("--headless")  # Optional: run without GUI
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
 
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.implicitly_wait(10)
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL",
        fix_hairline=True,
)
 
wait = WebDriverWait(driver, 15)
base_url = "https://www.healthline.com"
os.makedirs("healthline_html_pages", exist_ok=True)
 
for condition in all_conditions:
        print(f"\n🔍 Searching: {condition}")
 
        driver.get(base_url)
 
        # Accept cookie
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.css-whh5e5')))
            cookie_btn.click()
            print("🍪 Cookie accepted.")
        except:
            pass
 
        # Click search icon
        try:
            search_icon = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="nav-search-button"]')))
            #driver.execute_script("arguments[0].click();", search_icon)
            search_icon.click()
        except Exception as e:
            print(f"[ERROR] Search button not clickable: {e}")
            continue
 
        # Type condition in input field
        try:
            search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.autocomplete[name="q1"]')))
            search_input.clear()
            search_input.send_keys(condition)
            search_input.send_keys(Keys.ENTER)
        except:
            print("[ERROR] Could not type search.")
            continue
 
        # Wait for results and click the first one
        try:
            search_results = driver.find_element(By.ID, "__next")
            results = search_results.find_element(By.CLASS_NAME,"css-15x6pli")
            first_result = results.find_element(By.TAG_NAME, 'a')
            first_href = first_result.get_attribute("href")
            print(f"➡️ Opening article: {first_href}")
            driver.get(first_href)
        except Exception as e:
            print(e)
 
        # Wait for content to load
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            main = driver.find_element(By.ID, "__next")
            text = main.find_element(By.TAG_NAME, "article")
            article = BeautifulSoup(text.get_attribute("innerHTML"), "html.parser")
 
            # Extract main content
            #article = soup.find("div", class_=re.compile("css.*article.*body.*"))"""
            if not article:
                print(f"⚠️ Could not extract article body for '{condition}'")
                continue
 
            # Remove images, videos, scripts
            for tag in article.find_all(["img", "video", "script", "style"]):
                tag.decompose()
 
            # Final clean output
            cleaned_text = article.get_text(separator="\n", strip=True)
            html_clean = f"<html><head><meta charset='utf-8'><title>{condition}</title></head><body><pre>{cleaned_text}</pre></body></html>"
 
            filename = os.path.join("healthline_html_pages", f"{clean_condition_name(condition)}.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_clean)
 
            print(f"✅ Saved: {filename}")
 
        except Exception as e:
            print(f"⚠️ Could not process article for '{condition}': {e}")
 
 
driver.quit()
print("\n✅ All scraping completed.")