import re
import time
import os
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

def clean_condition_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# Leer CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")  

all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)

all_conditions = list(set(all_conditions))

# Configurar Selenium
options = Options()
# options.add_argument("--headless")  # Activa si no quieres ver el navegador
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 15)

base_url = "https://www.nhs.uk"

# Carpeta para guardar textos limpios
output_folder = "nhs_text_pages"
os.makedirs(output_folder, exist_ok=True)

for condition in all_conditions:
    print(f"\n[INFO] Searching for condition: '{condition}'")

    try:
        driver.get(base_url)
        time.sleep(2)

        # Aceptar cookies (nuevo banner superior izquierda)
        try:
            accept_cookies_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "nhsuk-cookie-banner__link_accept_analytics"))
            )
            accept_cookies_btn.click()
            print("[INFO] NHS analytics cookies accepted.")
            time.sleep(1)
        except:
            print("[INFO] No analytics cookie banner found or already accepted.")

        # Buscar condición
        search_box = wait.until(EC.presence_of_element_located((By.ID, "search-field")))
        search_box.clear()
        search_box.send_keys(condition)
        search_box.send_keys(Keys.ENTER)

        # Esperar resultados
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.nhsuk-list")))

        # Obtener links
        result_links = driver.find_elements(
            By.CSS_SELECTOR,
            "ul.nhsuk-list li.nhsuk-list-item--border h2.nhsuk-heading-xs a"
        )
        if not result_links:
            print(f"[WARNING] No search results found for '{condition}'. Skipping.")
            continue

        # Clic en el primer resultado
        first_link = result_links[0]
        first_link_href = first_link.get_attribute("href")
        print(f"[INFO] Opening first result: {first_link_href}")
        first_link.click()

        # Esperar a que cargue y extraer texto
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        for tag in soup(["script", "style", "img", "video", "svg", "iframe", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Guardar texto como .txt
        safe_name = clean_condition_name(condition)
        file_path = os.path.join(output_folder, f"{safe_name}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[INFO] Saved clean text to '{file_path}'")

    except Exception as e:
        print(f"[ERROR] Failed to process '{condition}': {e}")

driver.quit()
print("\n✅ All done! Check the 'nhs_text_pages' folder for saved files.")
