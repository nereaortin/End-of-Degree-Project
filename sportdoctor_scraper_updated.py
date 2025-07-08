import os
import re
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name.strip())

def start_browser():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--headless=new")  # Más rápido que el viejo headless
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 1,
        "profile.managed_default_content_settings.fonts": 2,
    })
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 8)
    return driver, wait

# Leer CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
conditions = []
for row in df["Related Conditions"].dropna():
    parts = re.split(r"[/\n]+", row)
    conditions.extend([p.strip() for p in parts if p.strip()])
conditions = list(set(conditions))

# Configuración
output_dir = "sportdoctor_txt_fast"
os.makedirs(output_dir, exist_ok=True)
BASE_URL = "https://sportdoctorlondon.com/"
RESTART_BROWSER_EVERY = 25

# Iniciar navegador
driver, wait = start_browser()

for i, condition in enumerate(conditions):
    print(f"\n🔍 Searching: {condition} ({i+1}/{len(conditions)})")

    # Reiniciar navegador cada X condiciones
    if i > 0 and i % RESTART_BROWSER_EVERY == 0:
        print("🔁 Restarting browser to stay fresh...")
        try: driver.quit()
        except: pass
        driver, wait = start_browser()

    try:
        driver.get(BASE_URL)

        # Cerrar cookies si aparecen
        try:
            cookie_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.sc-knesRu.ePGZca.amc-focus-first"))
            )
            cookie_btn.click()
        except:
            pass

        # Abrir buscador
        search_icon = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.fusion-main-menu-icon.fusion-bar-highlight"))
        )
        search_icon.click()

        # Buscar condición
        search_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']"))
        )
        search_input.clear()
        search_input.send_keys(condition)
        driver.find_element(By.CSS_SELECTOR, "input.fusion-search-submit.searchsubmit").click()

        # Clic en primer resultado
        first_result = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "h2.blog-shortcode-post-title.entry-title a"))
        )
        article_url = first_result.get_attribute("href")
        driver.get(article_url)

        # Esperar y parsear contenido
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Limpiar elementos no deseados
        for tag in soup(["script", "style", "img", "video", "iframe", "svg", "header", "footer", "nav", "aside"]):
            tag.decompose()
        main = soup.find("main") or soup.body
        clean_text = main.get_text(separator="\n", strip=True)

        # Guardar
        filename = os.path.join(output_dir, f"{clean_filename(condition)}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(clean_text)
        print(f"💾 Saved: {filename}")

    except Exception as e:
        print(f"❌ Error with '{condition}': {e}")
        time.sleep(random.uniform(1, 2))  # Sleep corto tras error

# Cerrar navegador al final
driver.quit()
print("\n✅ Finished scraping sportdoctorlondon.com!")
