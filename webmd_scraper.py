import re
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from multiprocessing import Pool, cpu_count

def clean_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.page_load_strategy = 'eager'
    chrome_prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2
    }
    chrome_options.add_experimental_option("prefs", chrome_prefs)
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrape_condition(condition):
    driver = setup_driver()
    wait = WebDriverWait(driver, 4)
    base_url = "https://www.webmd.com/"
    driver.get(base_url)

    try:
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            cookie_btn.click()
        except:
            pass

        try:
            search_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Search']")))
            search_btn.click()
        except:
            pass

        search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.webmd-input__inner")))
        search_input.send_keys(condition)

        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.search-results-title-link")))
        first_result = driver.find_element(By.CSS_SELECTOR, "a.search-results-title-link")
        driver.get(first_result.get_attribute("href"))

        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        html = driver.page_source

        file_name = clean_filename(condition) + ".html"
        with open(os.path.join("webmd_pages", file_name), "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[DONE] Saved: {condition}")

    except Exception as e:
        print(f"[ERROR] {condition}: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    os.makedirs("webmd_pages", exist_ok=True)
    df = pd.read_csv("exercises.csv", encoding="utf-8")
    conditions = []
    for row in df["Related Conditions"].dropna():
        splitted = re.split(r"[/\n]+", row)
        conditions.extend([c.strip() for c in splitted if c.strip()])
    conditions = list(set(conditions))

    with Pool(min(cpu_count(), 6)) as pool:  # Use up to 6 processes
        pool.map(scrape_condition, conditions)
