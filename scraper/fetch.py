import json, datetime, os, time, subprocess, sys



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



options = Options()

options.add_argument("--headless=new")

options.add_argument("--no-sandbox")

options.add_argument("--disable-dev-shm-usage")

options.add_argument("--disable-gpu")

options.add_argument("--window-size=1920,1080")



def check_bartow(driver):

    try:

        el = driver.find_element(By.NAME, "ctl00$ContentPlaceHolder1$as1$lstCounty$7")

        if not el.is_selected():

            driver.execute_script("arguments[0].click();", el)

            time.sleep(0.5)

        print("Bartow checked: " + str(el.is_selected()))

    except Exception as e:

        print("Bartow error: " + str(e))



print("Starting Chrome...")

driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 15)

records = []



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



        # Re-find bartow after postback refreshes DOM

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

            rows = tbl.find_all("tr")

            for row in rows[1:]:

                cells = row.find_all("td")

                if len(cells) >= 2:

                    txt = cells[0].get_text().strip()

                    if txt and len(txt) > 2 and txt.lower() not in ["name","notice","title","publication"]:

                        found += 1

                        rec = {

                            "name": txt,

                            "address": cells[1].get_text().strip() if len(cells) > 1 else "",

                            "date": cells[2].get_text().strip() if len(cells) > 2 else "",

                            "doc_type": cat_name,

                            "county": "Bartow",

                            "state": "GA"

                        }

                        records.append(rec)

                        print("  RECORD: " + str(rec))

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
