import os
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === Keywords relevantes para filtrar contenido ===
content_keywords = [
    "treatment", "treatments", "rehabilitation", "therapy", "physical therapy",
    "exercises", "exercise", "routine", "routines", "management", "stretch",
    "mobility", "home care", "recovery", "relief"
]

# === Leer condiciones desde el CSV ===
df = pd.read_csv("exercises.csv", encoding="utf-8")
conditions = set()
for row in df["Related Conditions"].dropna():
    for cond in re.split(r"[/\n]+", row):
        if cond.strip():
            conditions.add(cond.strip())

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name.strip().replace(" ", "_"))

# === Configurar navegador ===
options = Options()
# options.add_argument("--headless")  # Comenta esta línea si quieres ver el navegador
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

# === Carpeta de salida ===
output_dir = "downloads_pmc"
os.makedirs(output_dir, exist_ok=True)

# === Bucle por condición ===
for condition in conditions:
    print(f"\n🔍 Buscando en PMC: {condition}")
    try:
        driver.get("https://pmc.ncbi.nlm.nih.gov/")
        time.sleep(2)

        # Buscar usando ID real
        search_box = wait.until(EC.element_to_be_clickable((By.ID, "pmc-search")))
        search_box.clear()
        search_box.send_keys(condition)
        search_box.send_keys(Keys.ENTER)
        time.sleep(3)

        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.view[href*='/articles/PMC']")))
        links = driver.find_elements(By.CSS_SELECTOR, "a.view[href*='/articles/PMC']")

        best_link = None
        best_score = -1

        for link in links:
            title = link.text.lower()
            score = 0

            if condition.lower() in title:
                score += 3
            score += sum(1 for k in content_keywords if k in title)

            if score > best_score:
                best_score = score
                best_link = link

        if not best_link:
            print(f"⚠️ No se encontró artículo adecuado para: {condition}")
            continue

        print(f"➡️ Abriendo artículo: {best_link.text[:80]}...")
        driver.execute_script("arguments[0].click();", best_link)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        article = soup.find("div", id="maincontent") or soup.body
        if not article:
            print(f"❌ No se pudo extraer contenido del artículo: {condition}")
            continue

        relevant_text = []
        current_heading = ""

        # === Extraer secciones relevantes ===
        for tag in article.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "figure"]):
            text = tag.get_text(separator=" ", strip=True).lower()

            if tag.name.startswith("h"):
                current_heading = tag.get_text(strip=True)

            # Si es párrafo, lista o figura y contiene una keyword, lo guardamos
            if tag.name in ["p", "ul", "ol", "figure"]:
                if any(kw in text for kw in content_keywords):
                    relevant_text.append(f"{current_heading}\n{text}\n")

        # === Añadir referencias si existen ===
        references_section = article.find("section", id=re.compile("references?", re.I))
        if references_section:
            refs = references_section.get_text(separator="\n", strip=True)
            relevant_text.append("\nREFERENCIAS\n" + refs)

        # === Guardar solo si hay contenido relevante ===
        cleaned_output = "\n".join(relevant_text).strip()
        if not cleaned_output:
            cleaned_output = "[NO SE ENCONTRARON SECCIONES RELEVANTES]"

        filename = os.path.join(output_dir, f"{clean_filename(condition)}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(cleaned_output)

        print(f"✅ Guardado: {filename}")

    except Exception as e:
        print(f"❌ Error con '{condition}': {e}")
        continue

driver.quit()
print("\n🏁 Proceso completado.")
