import os
import re
import time
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

def clean_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# Cargar condiciones
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    items = re.split(r"[/\n]+", row)
    all_conditions.extend([i.strip() for i in items if i.strip()])
all_conditions = list(set(all_conditions))

# Configuración Selenium
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 12)

BASE_URL = "https://www.verywellhealth.com/"
SAVE_DIR = "verywellhealth_txt"
os.makedirs(SAVE_DIR, exist_ok=True)

for i, condition in enumerate(all_conditions):
    print(f"\n🔍 Searching: {condition} ({i + 1}/{len(all_conditions)})")
    try:
        driver.get(BASE_URL)

        # Aceptar cookies si aparece
        try:
            cookie_btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_btn.click()
            print("✅ Cookie accepted")
        except:
            print("ℹ️ No cookie popup appeared")

        # Hacer clic en la lupa de búsqueda
        try:
            search_icon = wait.until(EC.element_to_be_clickable((By.ID, "header-search-button_1-0")))
            search_icon.click()
        except:
            print("❌ Failed to click search icon.")
            continue

        # Buscar condición
        try:
            search_input = wait.until(EC.presence_of_element_located((By.ID, "search-input")))
            search_input.clear()
            search_input.send_keys(condition)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-bright.btn-go"))).click()
        except:
            print("❌ Failed to search.")
            continue

        # Esperar resultados y hacer clic en el segundo resultado
        time.sleep(3)
        results = driver.find_elements(By.CSS_SELECTOR, "li.comp.search-result-list-item.mntl-block a.comp.block.block-horizontal")
        if len(results) >= 2:
            link = results[1].get_attribute("href")
        elif results:
            link = results[0].get_attribute("href")
        else:
            print("❌ No results found.")
            continue

        driver.get(link)
        print(f"🔗 Navigated to: {link}")
        time.sleep(3)

        # Parsear y guardar solo texto
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "img", "video", "aside", "svg", "iframe"]):
            tag.decompose()

        main = soup.find("main") or soup.body
        if main:
            clean_text = main.get_text(separator="\n", strip=True)
            filename = os.path.join(SAVE_DIR, f"{clean_name(condition)}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(clean_text)
            print(f"💾 Saved: {filename}")
        else:
            print("⚠️ No main content found")

        time.sleep(2)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

driver.quit()
print("\n✅ Finished scraping Verywell Health.")
