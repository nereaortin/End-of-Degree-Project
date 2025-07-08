import re
import time
import os
import random
import threading
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
import winsound

RESTART_BROWSER_EVERY = 15
TIMEOUT_SECONDS = 15

def clean_condition_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name.strip())

keywords = [
    "exercise", "exercises", "routine", "routines", "warm up", "stretch", "stretches",
    "rehabilitation", "recovery", "treatment", "treatments", "therapy", "physical therapy",
    "management", "mobility", "relief", "improve", "motion", "strengthen", "strength", "home care"
]

df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = list(set(
    c.strip() for row in df["Related Conditions"].dropna()
    for c in re.split(r"[/\n]+", row) if c.strip()
))

output_folder = "mnt_txt_debug"
os.makedirs(output_folder, exist_ok=True)

def launch_browser():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def safe_restart_browser(timeout=10):
    result = [None]
    def do_restart():
        try: driver.quit()
        except: pass
        result[0] = launch_browser()
    t = threading.Thread(target=do_restart)
    t.start()
    t.join(timeout)
    if t.is_alive():
        print("❌ Reinicio colgado. Saltando condición.")
        return None
    print("[🔁] Navegador reiniciado.")
    return result[0]

def run_with_timeout(func, timeout):
    result = [None]
    def wrapper():
        try: result[0] = func()
        except Exception as e: result[0] = e
    t = threading.Thread(target=wrapper)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return TimeoutError("Timeout alcanzado")
    return result[0]

driver = launch_browser()
wait = WebDriverWait(driver, 10)

for i, condition in enumerate(all_conditions):
    print(f"\n🔍 [INFO] Buscando: '{condition}'")

    if i > 0 and i % RESTART_BROWSER_EVERY == 0:
        driver = safe_restart_browser()
        if driver is None: continue
        wait = WebDriverWait(driver, 10)

    def scrape():
        driver.get("https://www.medicalnewstoday.com/")
        time.sleep(0.5)

        try:
            for b in driver.find_elements(By.TAG_NAME, "button"):
                if any(t in b.text.lower() for t in ["accept", "continue"]):
                    b.click()
                    time.sleep(0.5)
                    break
        except: pass

        for btn in driver.find_elements(By.TAG_NAME, "button"):
            if "search" in (btn.get_attribute("aria-label") or "").lower():
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.6)
                break

        try:
            for b in driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Close']"):
                if b.is_displayed():
                    b.click()
                    time.sleep(0.3)
                    break
        except: pass

        search_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='q']")))
        search_input.clear()
        search_input.send_keys(condition)
        driver.execute_script("""
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, search_input)
        search_input.send_keys(Keys.ENTER)
        print("[OK] Búsqueda enviada.")
        time.sleep(1.5)

        if "verify that you are not a robot" in driver.page_source.lower():
            print("🔒 [AVISO] reCAPTCHA detectado. Esperando acción...")
            for _ in range(5): winsound.Beep(1000, 400); time.sleep(0.3)
            while "i'm not a robot" in driver.page_source.lower():
                print("[...] Esperando resolución manual...")
                time.sleep(2)
            print("✅ reCAPTCHA resuelto.")

        results = driver.find_elements(By.CSS_SELECTOR, "a.gs-title")
        if not results:
            print("❌ Sin resultados.")
            return

        best = None
        best_score = 0
        cl = condition.lower()
        for r in results:
            t = r.text.strip().lower()
            score = 3 if cl in t else 0
            score += sum(1 for k in keywords if k in t)
            if score > best_score:
                best_score = score
                best = r

        target = best if best else results[0]
        driver.execute_script("arguments[0].click();", target)
        time.sleep(1.5)

        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for tag in soup(["script", "style", "img", "video", "svg", "iframe", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else condition
        body = soup.get_text(separator="\n", strip=True)
        full_text = f"# {title}\n\n{body}"
        filename = os.path.join(output_folder, f"{clean_condition_name(condition)}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"[✅] Guardado: {filename}")

    result = run_with_timeout(scrape, TIMEOUT_SECONDS)
    if isinstance(result, TimeoutError):
        print(f"[⏱] Timeout en '{condition}', saltando...")

driver.quit()
print("\n✅ Scraping terminado. Archivos guardados en 'mnt_txt_debug'")
