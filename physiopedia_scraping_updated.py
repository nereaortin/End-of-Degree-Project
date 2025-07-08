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
from bs4 import BeautifulSoup

def clean_condition_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# Load and clean conditions
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = set()
for row in df["Related Conditions"].dropna():
    all_conditions.update([c.strip() for c in re.split(r"[/\n]+", row) if c.strip()])

# Setup faster Chrome options
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--disable-extensions")
options.add_argument("user-agent=Mozilla/5.0")
options.page_load_strategy = 'eager'  # Don't wait for every image and script

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)  

os.makedirs("physiopedia_html_pages", exist_ok=True)
base_url = "https://www.physio-pedia.com/home/"

for condition in all_conditions:
    if "click to purchase" in condition.lower():
        continue

    print(f"\n🔍 Searching for: {condition}")
    for attempt in range(2):  # try max 2 times
        try:
            driver.get(base_url)

            # Accept cookie
            try:
                cookie_btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]")))
                cookie_btn.click()
            except:
                pass

            # Search for the condition
            search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.pp-home-search.st-default-search-input")))
            driver.execute_script("arguments[0].value = arguments[1];", search_box, condition)
            search_box.send_keys(Keys.ENTER)

            time.sleep(1.5)  # minimal wait for results
            result_links = driver.find_elements(By.CSS_SELECTOR, "a.st-ui-result")
            if not result_links:
                print(f" No results for {condition}")
                break

            driver.get(result_links[0].get_attribute("href"))

            # Try clicking "Read this article" if it's blocking
            try:
                read_btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a#pp_content_hidden_cta_link")))
                read_btn.click()
                time.sleep(1)
            except:
                pass

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.mw-parser-output")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            content_div = soup.select_one("div.mw-parser-output")
            if not content_div:
                print(f" No content found for {condition}")
                break

            # Remove junk
            for selector in [
                "div.card.card-vertical",
                "div.pp_related_courses_wrap",
                "div#pp_content_hidden_msg_new_white_bg",
                "div#pp_content_hidden_cta_link",
                "div.st-module:has(.st-module-heading:-soup-contains('Related articles'))",
                "div.editors.tab-pane.active",
                "ul.nav.nav-tabs",
                "div.block-article-meta.block-article-meta-tabs",  # contents module
            ]:
                for tag in soup.select(selector):
                    tag.decompose()

            for p in content_div.find_all("p", recursive=False)[:5]:
                if any(kw in p.text.lower() for kw in ["original editor", "top contributors", "contributors"]):
                    p.decompose()

            for tag in content_div.find_all(["img", "video", "iframe", "figure"]):
                tag.decompose()

            toc = soup.select_one("div#toc")
            if toc:
                toc.decompose()

            # Extract from <h2> onward
            start = content_div.find("h2")
            html_content = ""
            while start:
                html_content += str(start)
                start = start.find_next_sibling()

            # Save
            full_html = f"<html><head><meta charset='utf-8'><title>{condition}</title></head><body>{html_content}</body></html>"
            file_path = os.path.join("physiopedia_html_pages", f"{clean_condition_name(condition)}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_html)

            print(f" Saved: {file_path}")
            time.sleep(random.uniform(1.5, 2.5))  # lower wait between pages
            break

        except Exception as e:
            print(f" Error for {condition} (Attempt {attempt + 1}): {e}")
            time.sleep(random.uniform(2, 4))

driver.quit()
print("\n Done! All pages saved.")
