from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import json
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Optional: suppress Chrome logs
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--log-level=3")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    # 1. Open the NHS website
    driver.get("https://www.nhs.uk/")

    # 2. Locate the search box and search for "cold symptoms"
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "search-field"))
    )
    print("Search box found!")
    search_box.send_keys("cold symptoms")
    search_box.send_keys(Keys.RETURN)

    # 3. Wait for the first matching result (li.nhsuk-list-item--border h2 a)
    first_result = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "li.nhsuk-list-item--border h2 a"))
    )
    print("First search result found!")

    # 4. Extract the link text & URL
    title = first_result.text
    url = first_result.get_attribute("href")
    print(f"Title: {title}")
    print(f"URL: {url}")

    # 5. Navigate to that link
    driver.get(url)
    time.sleep(2)  # wait for the page to load

    page_title = driver.title
    # Optionally scrape more info from the page (e.g., first paragraph)
    # For now, we'll keep it simple

    # 6. Save data to JSON
    result_data = {
        "search_title": title,
        "url": url,
        "page_title": page_title
    }

    with open("nhs_first_result.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=4)

    print("Data saved to 'nhs_first_result.json'.")

except Exception as e:
    print(f"Error: {e}")

finally:
    driver.quit()
