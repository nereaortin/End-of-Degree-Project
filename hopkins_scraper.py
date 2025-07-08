import re
import time
import os
import pandas as pd
from playwright.sync_api import sync_playwright

def clean_condition_name(name: str) -> str:
    """Sanitize the condition name to use as a filename."""
    return re.sub(r'[\\/*?:"<>|]', '_', name)

# Load related conditions from CSV
df = pd.read_csv("exercises.csv", encoding="utf-8")
all_conditions = []
for row in df["Related Conditions"].dropna():
    splitted = re.split(r"[/\n]+", row)
    splitted = [c.strip() for c in splitted if c.strip()]
    all_conditions.extend(splitted)
all_conditions = list(set(all_conditions))  # Remove duplicates

# Folder to store the final pages
os.makedirs("hopkins_html_pages", exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Set to True later if needed
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        viewport={'width': 1280, 'height': 800}
    )
    page = context.new_page()

    for condition in all_conditions:
        print(f"\n[INFO] Searching for condition: '{condition}'")

        try:
            # 1) Go to the website
            page.goto("https://www.hopkinsmedicine.org", timeout=60000)
            time.sleep(2)

            # 2) Handle cookie banner if it appears
            try:
                if page.locator("#onetrust-accept-btn-handler").is_visible():
                    page.click("#onetrust-accept-btn-handler")
                    print("[INFO] Cookie banner accepted.")
            except:
                print("[INFO] No cookie banner detected.")

            # 3) Click search icon
            page.click("button.toggle-ent-search.search-icon")
            page.wait_for_selector("input#header-search")
            print("[INFO] Clicked search icon.")

            # 4) Search for the condition
            search_input = page.locator("input#header-search")
            search_input.fill(condition)
            submit_btn = page.locator("button#header-search-submit")
            page.evaluate("(btn) => btn.click()", submit_btn)
            print("[INFO] Submitted search form.")
            page.wait_for_timeout(1500)

            # 5) Click first result
            first_result = page.wait_for_selector("a.search-results-title", timeout=15000)
            href = first_result.get_attribute("href")
            print(f"[INFO] Opening first result: {href}")
            first_result.click()

            # 6) Wait for the target page and save HTML
            page.wait_for_selector("h1", timeout=15000)
            page.wait_for_timeout(1500)
            page_html = page.content()

            safe_name = clean_condition_name(condition)
            file_path = os.path.join("hopkins_html_pages", f"{safe_name}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(page_html)
            print(f"[INFO] Saved HTML to '{file_path}'")

        except Exception as e:
            print(f"[ERROR] Failed to process '{condition}': {e}'")

    browser.close()

print("\n✅ All done! Check the 'hopkins_html_pages' folder for saved pages.")
