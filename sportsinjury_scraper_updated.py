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

# ---------------------------------------
# 🔧 CONFIGURACIÓN
# ---------------------------------------
BASE_URL = "https://www.sportsinjuryclinic.net"
OUTPUT_DIR = "sportsinjury_txt"
os.makedirs(OUTPUT_DIR, exist_ok=True)

KEYWORDS = [
    "exercise", "exercises", "routine", "routines", "warm up", "stretch", "stretches",
    "rehabilitation", "recovery", "treatment", "treatments", "therapy", "physical therapy",
    "management", "mobility", "relief", "improve", "motion", "strengthen", "strength", "home care"
]

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# ---------------------------------------
# 📄 Cargar condiciones del CSV
# ---------------------------------------
df = pd.read_csv("exercises.csv", encoding="utf-8")
conditions = set()
for row in df["Related Conditions"].dropna():
    for c in re.split(r"[/\n]+", row):
        if c.strip():
            conditions.add(c.strip())

# ---------------------------------------
# 🚀 Configurar navegador
# ---------------------------------------
options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless")  # Puedes descomentar para hacerlo sin abrir ventana
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

# ---------------------------------------
# 🔁 Bucle principal
# ---------------------------------------
for condition in conditions:
    print(f"\n🔍 Buscando: {condition}")
    try:
        driver.get(BASE_URL)
        time.sleep(1)

        # Aceptar cookies si aparece
        try:
            cookie_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fc-cta-consent"))
            )
            cookie_btn.click()
            print("✅ Cookies aceptadas")
        except:
            print("ℹ️ No cookies visibles")

        # Abrir búsqueda
        search_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.slide-search.astra-search-icon")))
        search_btn.click()

        search_input = wait.until(EC.visibility_of_element_located((By.ID, "search-field")))
        search_input.clear()
        search_input.send_keys(condition)
        search_input.send_keys(Keys.ENTER)
        time.sleep(2)

        # Buscar resultados
        results = driver.find_elements(By.CSS_SELECTOR, "p.ast-blog-single-element.ast-read-more-container.read-more > a")
        if not results:
            print("❌ No se encontraron resultados")
            continue

        best_link = None
        best_score = 0

        for link in results:
            href = link.get_attribute("href")
            title = link.text.lower()
            score = sum(1 for k in KEYWORDS if k in title)
            if condition.lower() in title:
                score += 5
            if score > best_score:
                best_score = score
                best_link = href

        if not best_link:
            best_link = results[0].get_attribute("href")

        print(f"➡️ Visitando: {best_link}")
        driver.get(best_link)
        time.sleep(3)

        # Extraer solo texto
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "svg", "noscript"]):
            tag.decompose()

        article = soup.find("article") or soup.body
        text = article.get_text(separator="\n", strip=True)

        # Guardar como .txt
        file_path = os.path.join(OUTPUT_DIR, f"{clean_filename(condition)}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ Guardado: {file_path}")

    except Exception as e:
        print(f"❌ Error para '{condition}': {e}")

driver.quit()
print("\n🏁 Finalizado. Archivos guardados en carpeta 'sportsinjury_txt'")
