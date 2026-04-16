import json, datetime, os, time, subprocess, sys, re

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "--quiet"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

OUTPUT_FILE = "dashboard/records.json"
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=30)
print("Running: " + str(start_date) + " to " + str(end_date))

def extract_name(text):
    t = text.replace("\n", " ")
    m = re.search(r'executed by ([A-Z][A-Z\s,\.]+?)(?:\s+to\s+|\s+hereinafter|\s+as\s+Grantor|,\s+as\s+)', t)
    if m:
        return m.group(1).strip().rstrip(",").strip()
    m = re.search(r'[Ee]state of ([A-Za-z\s,\.]+?)(?:,\s*deceased|,\s*late)', t)
    if m:
        return "Estate of " + m.group(1).strip()
    m = re.search(r'\bby ([A-Z][A-Z\s,\.]+?) to\b', t)
    if m:
        return m.group(1).strip().rstrip(",").strip()
    return ""

def extract_address(text):
    t = text.replace("\n", " ")
    m = re.search(r'(?:known as|located at|property known as|property at)[:\s]+([0-9][^\.,;]{5,60}(?:GA|Georgia)[^,]{0,10})', t, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r'(\d+\s+[A-Za-z][^\n,]{3,50}(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Way|Blvd|Court|Ct|Hwy)[^\n,]{0,40})', t, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r'([A-Za-z\s]+,\s*(?:Georgia|GA)\s*\d{5})', t)
    if m:
        return m.group(1).strip()
    m = re.search(r'nCity:\s*([A-Za-z\s]+)', t)
    if m:
        return m.group(1).strip() + ", GA"
    return ""

def extract_date(text):
    t = text.replace("\n", " ")
    m = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', t)
    if m:
        return m.group(0)
    return ""

def check_bartow(driver):
    try:
        el = driver.find_element(By.NAME, "ctl00$ContentPlaceHolder1$as1$lstCounty$7")
        if not el.is_selected():
            driver.execute_script("arguments[0].click();", el)
            time.sleep(0.5)
        print("Bartow checked: " + str(el.is_selected()))
    except Exception as e:
        print("Bartow error: " + str(e))

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

print("Starting Chrome...")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)
records = []
seen = set()

CATEGORIES = ["Foreclosures", "Debtors and Creditors", "Sheriff's/Marshal's Sales"]

try:
    for cat_name in CATEGORIES:
        print("\n=== " + cat_name + " ===")
        driver.get("https://georgiapublicnotice.com")
        time.sleep(3)

        check_bartow(driver)

        try:
            ddl = wait.until(EC.presence_of_element_located(
                (By.NAME, "ctl00$ContentPlaceHolder1$as1$ddlPopularSearches")))
            Select(ddl).select_by_visible_text(cat_name)
            print("Category selected")
            time.sleep(3)
        except Exception as e:
            print("Dropdown error: " + str(e))
            continue

        check_bartow(driver)

        try:
            btn = wait.until(EC.presence_of_element_located(
                (By.NAME, "ctl00$ContentPlaceHolder1$as1$btnGo")))
            driver.execute_script("arguments[0].click();", btn)
            print("Search clicked")
            time.sleep(5)
        except Exception as e:
            print("Button error: " + str(e))
            continue

        print("URL: " + driver.current_url)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        found = 0
        for tbl in soup.find_all("table"):
            for row in tbl.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) < 1:
                    continue
                full_text = cells[0].get_text()
                if len(full_text) < 50:
                    continue

                name = extract_name(full_text)
                address = extract_address(full_text)
                date = extract_date(full_text)

                if not name:
                    continue

                key = name + "|" + cat_name
                if key in seen:
                    continue
                seen.add(key)

                found += 1
                rec = {
                    "name": name,
                    "address": address,
                    "date": date,
                    "doc_type": cat_name,
                    "county": "Bartow",
                    "state": "GA",
                    "raw": full_text[:200].replace("\n", " ").strip()
                }
                records.append(rec)
                print("  NAME: " + name)
                print("  ADDR: " + address)
                print("  DATE: " + date)
                print("  ---")

        print("Found: " + str(found))

finally:
    driver.quit()
    print("Browser closed")

print("\nTOTAL: " + str(len(records)))
os.makedirs("dashboard", exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump({
        "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",
        "date_range": {"start": str(start_date), "end": str(end_date)},
        "county": "Bartow",
        "state": "GA",
        "total": len(records),
        "records": records
    }, f, indent=2)
print("Saved to " + OUTPUT_FILE)
