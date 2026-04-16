import json, datetime, os, time, sys, re, subprocess, os



subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "beautifulsoup4", "--quiet"])



from selenium import webdriver

from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait, Select

from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import StaleElementReferenceException

from bs4 import BeautifulSoup



OUTPUT_FILE = "dashboard/records.json"

end_date = datetime.date.today()

start_date = end_date - datetime.timedelta(days=30)

print("Running: " + str(start_date) + " to " + str(end_date))



BARTOW_NAME = "ctl00$ContentPlaceHolder1$as1$lstCounty$7"



def safe_check_bartow(driver):

    """Retry up to 5 times — handles PostBack re-render stale element."""

    for attempt in range(5):

        try:

            time.sleep(1.5)

            els = driver.find_elements(By.NAME, BARTOW_NAME)

            if not els:

                print("  Bartow not found, waiting... attempt " + str(attempt + 1))

                time.sleep(2)

                continue

            el = els[0]

            if not el.is_selected():

                driver.execute_script("arguments[0].click();", el)

                time.sleep(1)

                els2 = driver.find_elements(By.NAME, BARTOW_NAME)

                if els2 and els2[0].is_selected():

                    print("  Bartow: CHECKED OK")

                    return True

                else:

                    print("  Bartow: click did not stick, retry...")

                    time.sleep(2)

            else:

                print("  Bartow: already checked")

                return True

        except StaleElementReferenceException:

            print("  Bartow stale, retry " + str(attempt + 1))

            time.sleep(2)

        except Exception as e:

            print("  Bartow error: " + str(e))

            time.sleep(1)

    print("  WARNING: Could not confirm Bartow checkbox!")

    return False



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

    m = re.search(r'(?:known as|located at|property known as|property at)[:\s]+([0-9][^\.,;]{5,80}(?:GA|Georgia)[^,\.]{0,20})', t, re.IGNORECASE)

    if m:

        return m.group(1).strip()

    m = re.search(r'(\d+\s+[A-Za-z][^\n,]{3,60}(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Drive|Dr\.?|Lane|Ln\.?|Way|Blvd|Court|Ct\.?|Hwy|Highway|Circle|Cir)[^\n,]{0,50})', t, re.IGNORECASE)

    if m:

        return m.group(1).strip()

    m = re.search(r'([A-Za-z\s]+,\s*(?:Georgia|GA)\s*\d{5})', t)

    if m:

        return m.group(1).strip()

    return ""



def extract_date(text):

    t = text.replace("\n", " ")

    m = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', t)

    if m:

        return m.group(0)

    return ""



options = Options()

options.add_argument("--headless=new")

options.add_argument("--no-sandbox")

options.add_argument("--disable-dev-shm-usage")

options.add_argument("--disable-gpu")

options.add_argument("--window-size=1920,1080")



print("Starting Chrome...")

driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 20)

records = []

seen = set()



CATEGORIES = ["Foreclosures", "Debtors and Creditors", "Sheriff's/Marshal's Sales"]



try:

    for cat_name in CATEGORIES:

        print("\n=== " + cat_name + " ===")

        driver.get("https://georgiapublicnotice.com")

        time.sleep(5)  # Let ASP.NET fully render



        # Step 1: Check Bartow BEFORE dropdown

        safe_check_bartow(driver)



        # Step 2: Select category (triggers PostBack — DOM re-renders)

        try:

            ddl = wait.until(EC.element_to_be_clickable(

                (By.NAME, "ctl00$ContentPlaceHolder1$as1$ddlPopularSearches")))

            Select(ddl).select_by_visible_text(cat_name)

            print("Category selected: " + cat_name)

            time.sleep(5)  # Wait for PostBack to complete

        except Exception as e:

            print("Dropdown error: " + str(e))

            continue



        # Step 3: Re-check Bartow AFTER PostBack (DOM was rebuilt)

        safe_check_bartow(driver)



        # Step 4: Click Search

        try:

            btn = wait.until(EC.element_to_be_clickable(

                (By.NAME, "ctl00$ContentPlaceHolder1$as1$btnGo")))

            driver.execute_script("arguments[0].click();", btn)

            print("Search clicked")

            time.sleep(6)

        except Exception as e:

            print("Button error: " + str(e))

            continue



        print("URL: " + driver.current_url)



        # Step 5: Scrape all pages

        page_num = 1

        cat_found = 0

        first_raw_printed = False



        while True:

            print("  Page " + str(page_num))

            soup = BeautifulSoup(driver.page_source, "html.parser")

            rows_this_page = 0



            for tbl in soup.find_all("table"):

                for row in tbl.find_all("tr")[1:]:

                    cells = row.find_all("td")

                    if not cells:

                        continue

                    full_text = cells[0].get_text()

                    if len(full_text) < 50:

                        continue



                    rows_this_page += 1



                    # Print first raw sample per category for debugging

                    if not first_raw_printed:

                        print("  SAMPLE RAW: " + full_text[:400].replace("\n", " "))

                        first_raw_printed = True



                    name    = extract_name(full_text)

                    address = extract_address(full_text)

                    date    = extract_date(full_text)



                    if not name:

                        continue



                    key = name + "|" + cat_name

                    if key in seen:

                        continue

                    seen.add(key)



                    cat_found += 1

                    records.append({

                        "name":     name,

                        "address":  address,

                        "date":     date,

                        "doc_type": cat_name,

                        "county":   "Bartow",

                        "state":    "GA",

                        "raw":      full_text[:300].replace("\n", " ").strip()

                    })

                    print("  NAME: " + name)

                    print("  ADDR: " + address)

                    print("  DATE: " + date)

                    print("  ---")



            print("  Rows found this page: " + str(rows_this_page))



            # Pagination

            next_clicked = False

            try:

                for link_text in [">", "Next", "Next >"]:

                    try:

                        nxt = driver.find_element(By.LINK_TEXT, link_text)

                        driver.execute_script("arguments[0].click();", nxt)

                        time.sleep(4)

                        next_clicked = True

                        print("  -> Next page")

                        break

                    except:

                        pass

            except:

                pass



            if not next_clicked or page_num >= 10:

                break

            page_num += 1



        print("Category total: " + str(cat_found))



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
