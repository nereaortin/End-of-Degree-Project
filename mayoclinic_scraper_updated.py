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
from bs4 import BeautifulSoup

def clean_condition_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# Palabras clave relevantes (ejercicio, tratamiento, rehabilitación, etc.)
keywords = [
    "exercise", "exercises", "routine", "routines", "warm up", "stretch", "stretches",
    "rehabilitation", "recovery", "treatment", "treatments", "therapy", "physical therapy",
    "management", "mobility", "relief", "improve", "motion", "strengthen", "strength", "home care"
]

# Leer CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")  
all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)
all_conditions = list(set(all_conditions))

# Configuración de Selenium
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-accelerated-2d-canvas")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless=new")  # Comentarlo para ver el navegador

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 6)

base_url = "https://www.mayoclinic.org"
os.makedirs("mayo_clean_pages", exist_ok=True)

# Loop principal
for condition in all_conditions:
    print(f"\n🔍 Searching for: '{condition}'")

    try:
        driver.get(base_url)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.cmp-search-button button"))).click()

        search_box = wait.until(EC.presence_of_element_located((By.ID, "search-input-globalsearch-773693aac3")))
        search_box.clear()
        search_box.send_keys(condition)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.search-button.sc-mc-search[type='submit']"))).click()

        # Esperar a que carguen resultados
        results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.azsearchlink")))

        selected_result = None
        for result in results:
            title = result.text.lower()
            if any(keyword in title for keyword in keywords):
                selected_result = result
                break

        if not selected_result:
            print("⚠️ No se encontró ningún resultado con palabras clave relevantes.")
            continue

        result_url = selected_result.get_attribute("href")
        print(f"➡️ Abriendo: {result_url}")
        driver.get(result_url)

        # Esperar contenido del artículo
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        for tag in soup(["script", "style", "img", "iframe", "video", "noscript", "svg"]):
            tag.decompose()

        main_content = soup.find("article", id="main-content")
        if not main_content:
            print(f"[WARN] No se encontró <article id='main-content'> para '{condition}'")
            continue

        clean_html = main_content.prettify()
        safe_name = clean_condition_name(condition)
        file_path = os.path.join("mayo_clean_pages", f"{safe_name}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(clean_html)
        print(f"✅ Guardado limpio: '{file_path}'")

    except Exception as e:
        print(f"❌ Error en '{condition}': {e}")

driver.quit()
print("\n🚀 ¡Listo! Archivos en la carpeta 'mayo_clean_pages'")
