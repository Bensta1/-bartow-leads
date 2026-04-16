import json, datetime, os, requests

from bs4 import BeautifulSoup



OUTPUT_FILE = "dashboard/records.json"

BASE_URL = "https://georgiapublicnotice.com/default.aspx"

COUNTY   = "ctl00$ContentPlaceHolder1$as1$lstCounty$7"

DDL      = "ctl00$ContentPlaceHolder1$as1$ddlPopularSearches"

BTN      = "ctl00$ContentPlaceHolder1$as1$btnGo"

TXT      = "ctl00$ContentPlaceHolder1$as1$txtSearch"



def get_state(soup):

    vs  = soup.find("input", {"name": "__VIEWSTATE"})

    vsg = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})

    ev  = soup.find("input", {"name": "__EVENTVALIDATION"})

    return (vs["value"] if vs else "", vsg["value"] if vsg else "", ev["value"] if ev else "")



session = requests.Session()

session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"})



print("Step 0: Initial GET")

r0 = session.get(BASE_URL, timeout=20)

print("GET: " + str(r0.status_code))

soup0 = BeautifulSoup(r0.text, "html.parser")

vs, vsg, ev = get_state(soup0)

print("VS length: " + str(len(vs)))



records = []



for cat_val, cat_name in [("16","Foreclosures"), ("24","Sheriffs Sales"), ("12","Debtors and Creditors")]:

    print("\n====== " + cat_name + " ======")



    # STEP 1 — AutoPostBack: select category from dropdown

    print("Step 1: Select category")

    s1 = {

        "__VIEWSTATE":          vs,

        "__VIEWSTATEGENERATOR": vsg,

        "__EVENTVALIDATION":    ev,

        "__EVENTTARGET":        DDL,

        "__EVENTARGUMENT":      "",

        "__LASTFOCUS":          "",

        DDL:                    cat_val,

        COUNTY:                 "on",

        TXT:                    "",

    }

    r1 = session.post(BASE_URL, data=s1, timeout=30)

    print("Step1 status: " + str(r1.status_code))

    soup1 = BeautifulSoup(r1.text, "html.parser")

    vs2, vsg2, ev2 = get_state(soup1)

    print("New VS length: " + str(len(vs2)))

    print("Step1 snippet: " + soup1.get_text()[300:600].replace("\n"," "))



    # STEP 2 — Click Search button with refreshed ViewState

    print("Step 2: Click Search")

    s2 = {

        "__VIEWSTATE":          vs2,

        "__VIEWSTATEGENERATOR": vsg2,

        "__EVENTVALIDATION":    ev2,

        "__EVENTTARGET":        "",

        "__EVENTARGUMENT":      "",

        "__LASTFOCUS":          "",

        DDL:                    cat_val,

        COUNTY:                 "on",

        TXT:                    "",

        BTN:                    "Search",

    }

    r2 = session.post(BASE_URL, data=s2, timeout=30)

    print("Step2 status: " + str(r2.status_code))

    soup2 = BeautifulSoup(r2.text, "html.parser")

    print("Step2 snippet: " + soup2.get_text()[300:800].replace("\n"," "))



    found = 0

    for tbl in soup2.find_all("table"):

        rows = tbl.find_all("tr")

        for row in rows[1:]:

            cells = row.find_all("td")

            if len(cells) >= 2:

                txt = cells[0].get_text().strip()

                if txt and len(txt) > 2:

                    found += 1

                    records.append({

                        "name":     txt,

                        "address":  cells[1].get_text().strip() if len(cells) > 1 else "",

                        "date":     cells[2].get_text().strip() if len(cells) > 2 else "",

                        "doc_type": cat_name,

                        "county":   "Bartow",

                        "state":    "GA"

                    })

    print("Found: " + str(found))



print("\nTOTAL: " + str(len(records)))

os.makedirs("dashboard", exist_ok=True)

with open(OUTPUT_FILE, "w") as f:

    json.dump({"fetched_at": datetime.datetime.utcnow().isoformat()+"Z", "county": "Bartow", "state": "GA", "total": len(records), "records": records}, f, indent=2)

print("Saved to " + OUTPUT_FILE)
