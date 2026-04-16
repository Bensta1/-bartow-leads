import json, datetime, os, requests

from bs4 import BeautifulSoup



OUTPUT_FILE = "dashboard/records.json"

LOOKBACK_DAYS = 30

end_date = datetime.date.today()

start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)

print("Running: " + str(start_date) + " to " + str(end_date))



session = requests.Session()

session.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"})

BASE = "https://georgiapublicnotice.com"

resp = session.get(BASE, timeout=20)

print("GET: " + str(resp.status_code))

soup = BeautifulSoup(resp.text, "html.parser")



for form in soup.find_all("form"):

    print("FORM action=" + str(form.get("action","")) + " method=" + str(form.get("method","")))



vs  = soup.find("input", {"name": "__VIEWSTATE"})

vsg = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})

ev  = soup.find("input", {"name": "__EVENTVALIDATION"})

viewstate     = vs["value"]  if vs  else ""

viewstate_gen = vsg["value"] if vsg else ""

event_val     = ev["value"]  if ev  else ""



COUNTY = "ctl00$ContentPlaceHolder1$as1$lstCounty$7"

DDL    = "ctl00$ContentPlaceHolder1$as1$ddlPopularSearches"



records = []



# Numeric values from the SELECT options we found in logs

for cat_val, cat_name in [("16","Foreclosures"), ("24","Sheriff Sales"), ("12","Debtors and Creditors")]:

    print("--- " + cat_name + " (val=" + cat_val + ") ---")

    post_data = {

        "__VIEWSTATE":          viewstate,

        "__VIEWSTATEGENERATOR": viewstate_gen,

        "__EVENTVALIDATION":    event_val,

        "__EVENTTARGET":        DDL,

        "__EVENTARGUMENT":      "",

        "__LASTFOCUS":          "",

        DDL:                    cat_val,

        COUNTY:                 "on",

    }

    r = session.post(BASE, data=post_data, timeout=30)

    print("POST: " + str(r.status_code))

    rsoup = BeautifulSoup(r.text, "html.parser")

    print("Snippet: " + rsoup.get_text()[200:600].replace("\n"," "))

    found = 0

    for tbl in rsoup.find_all("table"):

        rows = tbl.find_all("tr")

        for row in rows[1:]:

            cells = row.find_all("td")

            if len(cells) >= 2:

                name_text = cells[0].get_text().strip()

                if name_text and len(name_text) > 2:

                    found += 1

                    records.append({"name": name_text, "address": cells[1].get_text().strip() if len(cells) > 1 else "", "date": cells[2].get_text().strip() if len(cells) > 2 else "", "doc_type": cat_name, "county": "Bartow", "state": "GA"})

    print("Found: " + str(found))



print("TOTAL: " + str(len(records)))

os.makedirs("dashboard", exist_ok=True)

with open(OUTPUT_FILE, "w") as f:

    json.dump({"fetched_at": datetime.datetime.utcnow().isoformat() + "Z", "county": "Bartow", "state": "GA", "total": len(records), "records": records}, f, indent=2)

print("Saved to " + OUTPUT_FILE)
