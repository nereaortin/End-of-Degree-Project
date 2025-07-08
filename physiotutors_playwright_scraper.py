
import re
import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.physiotutors.com/"
OUTPUT_DIR = "physiotutors_txt_playwright"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# Leer condiciones desde CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
conditions = list(set(
    c.strip() for r in df["Related Conditions"].dropna()
    for c in re.split(r"[/\n]+", r) if c.strip()
))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    for condition in conditions:
        print(f"\n🔍 Buscando: {condition}")
        try:
            page.goto(BASE_URL, timeout=15000)
            time.sleep(1)

            # Aceptar cookies
            try:
                page.click("button.cmplz-btn.cmplz-accept", timeout=3000)
                print("[OK] Cookies aceptadas.")
            except:
                print("[INFO] No cookies visibles.")

            # Abrir buscador
            page.click("div.site-header__search-toggle", timeout=4000)
            page.fill("input.c-search-bar__form-input", re.sub(r"[^\w\s\-]", "", condition))
            page.keyboard.press("Enter")
            print("[OK] Búsqueda enviada.")
            page.wait_for_timeout(1200)

            # Clic en primer resultado
            page.click("a.s-site-search__post-link", timeout=5000)
            page.wait_for_timeout(1500)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "svg"]):
                tag.decompose()

            main = soup.find("main") or soup.find("div", class_="post-content") or soup.body
            if not main:
                print("[❌] No se pudo extraer el contenido.")
                continue

            title_tag = main.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else condition

            parts = [f"# {title}"]
            for el in main.descendants:
                if el.name == "img" and el.has_attr("src"):
                    parts.append(f"[IMAGE] {el['src']}")
                elif el.name in ("video", "source", "iframe") and el.has_attr("src"):
                    parts.append(f"[MEDIA] {el['src']}")
                elif isinstance(el, str):
                    clean = el.strip()
                    if clean:
                        parts.append(clean)

            filename = os.path.join(OUTPUT_DIR, f"{clean_filename(condition)}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(parts))

            print(f"[✅] Guardado en '{filename}'")
        except Exception as e:
            print(f"[❌ ERROR en '{condition}']: {e}")
            continue

    browser.close()
