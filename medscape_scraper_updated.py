import os
import re
import time
import winsound
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
    return re.sub(r'[\\/*?:"<>|]', '_', name.strip())

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--start-maximized")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def alert_user_to_login():
    print("\n🔐 Inicia sesión manualmente en Medscape.")
    for _ in range(3):
        winsound.Beep(1000, 600)
        time.sleep(0.5)
    input("⏳ Pulsa Enter cuando hayas terminado de iniciar sesión...")

# Leer condiciones desde CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    for cond in re.split(r"[/\n]+", row):
        if cond.strip():
            all_conditions.append(cond.strip())

all_conditions = list(set(all_conditions))

# Inicializar navegador
driver = init_driver()
wait = WebDriverWait(driver, 10)

# --- Login manual al principio ---
driver.get("https://www.medscape.com/")
time.sleep(2)
try:
    cookie_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'I Accept')]"))
    )
    cookie_btn.click()
except:
    pass

# Click en botón "Log In"
try:
    login_button = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//a[contains(text(), 'Log In')]"
    )))
    login_button.click()
except:
    print("[⚠️] No se encontró botón de login.")

# Avisar para login manual
alert_user_to_login()

# Crear carpeta para guardar .txt
os.makedirs("medscape_text_pages", exist_ok=True)

# Bucle principal
for i, condition in enumerate(all_conditions):
    print(f"\n🔍 Buscando: '{condition}'")
    try:
        driver.get("https://www.medscape.com/")
        time.sleep(1.5)

        search_box = wait.until(EC.presence_of_element_located((By.ID, "search-input")))
        search_box.clear()
        search_box.send_keys(condition)
        search_box.send_keys(Keys.ENTER)

        # Clic en primer resultado
        result_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "p.searchResultTitle a"))
        )
        result_link.click()
        time.sleep(3)

        # Detectar si nos sacó de la sesión (formulario de login)
        try:
            wait.until(EC.presence_of_element_located((
                By.XPATH, "//span[contains(@class, 'mdscp-form-title') and contains(text(), 'Log in or register')]"
            )))
            print("[⚠️] Se cerró sesión. Esperando login manual...")
            alert_user_to_login()

            # Volver a buscar la condición después del login
            driver.get("https://www.medscape.com/")
            time.sleep(1.5)
            search_box = wait.until(EC.presence_of_element_located((By.ID, "search-input")))
            search_box.clear()
            search_box.send_keys(condition)
            search_box.send_keys(Keys.ENTER)

            result_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.searchResultTitle a"))
            )
            result_link.click()
            time.sleep(3)

        except:
            pass

        # Extraer texto visible
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        html_content = driver.page_source

        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "img", "svg", "iframe", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        main = soup.find("main") or soup.body
        text = main.get_text(separator="\n", strip=True)

        # Guardar como .txt
        file_name = clean_condition_name(condition) + ".txt"
        with open(os.path.join("medscape_text_pages", file_name), "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ Guardado: '{file_name}'")
        time.sleep(1)

    except Exception as e:
        print(f"[ERROR] Falló para '{condition}': {e}")

driver.quit()
print("\n✅ ¡Listo! Archivos guardados en 'medscape_text_pages'.")
