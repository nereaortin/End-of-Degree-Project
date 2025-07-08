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
    return re.sub(r'[\\/*?:"<>|]', '_', name.strip())

# 1) Load conditions from CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    for cond in re.split(r"[/\n]+", row):
        if cond.strip():
            all_conditions.append(cond.strip())

# Remove duplicates
all_conditions = list(set(all_conditions))

# 2) Selenium setup
options = Options()
# options.add_argument("--headless")  # Uncomment if you don't want to see the browser
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors=yes")
options.add_argument(
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/98.0.4758.102 Safari/537.36'
)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 30)

base_url = "https://www.hss.edu/conditions.asp"

# 3) Create output folder
os.makedirs("hss_text_pages", exist_ok=True)

for condition in all_conditions:
    print(f"\n🔍 Buscando: '{condition}'")

    try:
        # Go to HSS search page
        driver.get(base_url)
        time.sleep(2)

        # Wait for and use search box
        search_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                "input.st-default-search-input[placeholder='Search Conditions and Treatments']"))
        )
        search_box.clear()
        search_box.send_keys(condition)
        time.sleep(1)
        search_box.send_keys(Keys.ENTER)

        # Wait for results
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "st-ui-result")))
        time.sleep(2)

        # Click on first search result
        anchor = driver.find_element(
            By.CSS_SELECTOR,
            "#centercolumn > div > div > div > div > div > div.st-ui-container-primary_content.st-position-container > div.st-ui-injected-content.st-search-results > div > a:nth-child(1)"
        )
        href = anchor.get_attribute("href")
        print(f"[INFO] Opening: {href}")

        # Try normal click or JS click or direct nav
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", anchor)
            time.sleep(1)
            anchor.click()
        except:
            try:
                driver.execute_script("arguments[0].click();", anchor)
            except:
                driver.get(href)

        # Wait for page to load
        wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
        time.sleep(2)

        # Extract visible text only
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for tag in soup(["script", "style", "img", "svg", "iframe", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        main = soup.find("main") or soup.body
        text = main.get_text(separator="\n", strip=True)

        # Save text file
        filename = os.path.join("hss_text_pages", f"{clean_condition_name(condition)}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ Guardado: {filename}")

    except Exception as e:
        print(f"❌ Error con '{condition}': {e}")

    time.sleep(4)

driver.quit()
print("\n🏁 Todo listo. Archivos guardados en 'hss_text_pages'.")
