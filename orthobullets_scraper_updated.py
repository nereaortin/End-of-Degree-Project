import re
import os
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

# Leer condiciones desde CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
conditions = set()
for row in df["Related Conditions"].dropna():
    for cond in re.split(r"[/\n]+", row):
        if cond.strip():
            conditions.add(cond.strip())

def clean_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name.strip())

# Configurar navegador
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

output_dir = "orthobullets_txt"
os.makedirs(output_dir, exist_ok=True)

for condition in conditions:
    print(f"\n🔍 Buscando: {condition}")
    try:
        driver.get("https://www.orthobullets.com/")
        search_box = wait.until(EC.element_to_be_clickable((By.ID, "searchbox")))
        search_box.clear()
        search_box.send_keys(condition)
        search_box.send_keys(Keys.ENTER)

        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.dashboard-item__link")))
        links = driver.find_elements(By.CSS_SELECTOR, "a.dashboard-item__link")

        target_link = None

        for link in links:
            try:
                # Buscar div que contiene el icono azul
                icon_container = link.find_element(
                    By.CSS_SELECTOR,
                    "div.dashboard-item__image-label.content-type-label--topic"
                )
                donut_icon = icon_container.find_element(By.CSS_SELECTOR, "i.icon.icon-donut")
                if donut_icon:
                    target_link = link
                    break
            except:
                continue

        if target_link:
            driver.execute_script("arguments[0].scrollIntoView(true);", target_link)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", target_link)
        else:
            print("⚠️ No se encontró un resultado con el icono donut azul.")
            continue

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        for tag in soup(["script", "style", "img", "svg", "video", "iframe", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        main = soup.find("main") or soup.body
        text = main.get_text(separator="\n", strip=True)

        filename = os.path.join(output_dir, f"{clean_filename(condition)}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"[✅] Guardado: {filename}")

    except Exception as e:
        print(f"[❌ ERROR] Para '{condition}': {e}")

driver.quit()
print("\n🏁 Listo. Archivos guardados en la carpeta 'orthobullets_txt'")
