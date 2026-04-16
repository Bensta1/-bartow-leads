import json, datetime, os, requests

from bs4 import BeautifulSoup



OUTPUT_FILE = "dashboard/records.json"

LOOKBACK_DAYS = 30

end_date = datetime.date.today()

start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)

print("Running: " + str(start_date) + " to " + str(end_date))



session = requests.Session()

session.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"})

resp = session.get("https://georgiapublicnotice.com", timeout=20)

soup = BeautifulSoup(resp.text, "html.parser")



vs  = soup.find("input", {"name": "__VIEWSTATE"})

vsg = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})

ev  = soup.find("input", {"name": "__EVENTVALIDATION"})

viewstate     = vs["value"]  if vs  else ""

viewstate_gen = vsg["value"] if vsg else ""

event_val     = ev["value"]  if ev  else ""



# Find county checkboxes and their labels

print("=== COUNTY LIST ===")

bartow_field = None

for inp in soup.find_all("input", {"type": "checkbox"}):

    n = inp.get("name", "")

    if "lstCounty" in n:

        label = inp.find_next("label")

        label_text = label.get_text().strip() if label else inp.find_next(string=True).strip() if inp.find_next(string=True) else "?"

        print(n + " = " + label_text)

        if "Bartow" in label_text or "bartow" in label_text.lower():

            bartow_field = n

            print("^^^ BARTOW FOUND: " + n)



print("=== ALL SELECTS ===")

for sel in soup.find_all("select"):

    n = sel.get("name", "")

    opts = [o.get("value","") + "=" + o.get_text().strip() for o in sel.find_all("option")]

    print("SELECT name=" + n + " options=" + str(opts[:20]))



# Now try actual search with correct field names

BTN = "ctl00$ContentPlaceHolder1$as1$btnGo"

TXT = "ctl00$ContentPlaceHolder1$as1$txtSearch"

COUNTY = bartow_field if bartow_field else "ctl00$ContentPlaceHolder1$as1$lstCounty$7"

print("Using county field: " + COUNTY)



records = []

for term in ["foreclosure", "lien"]:

    print("Searching: " + term)

    post_data = {

        "__VIEWSTATE":          viewstate,

        "__VIEWSTATEGENERATOR": viewstate_gen,

        "__EVENTVALIDATION":    event_val,

        "__EVENTTARGET":        "",

        "__EVENTARGUMENT":      "",

        "__LASTFOCUS":          "",

        TXT:                    term,

        "ctl00$ContentPlaceHolder1$as1$rdoType": "OR",

        COUNTY:                 "on",

        BTN:                    "Search"

    }

    r = session.post("https://georgiapublicnotice.com", data=post_data, timeout=30)

    print("POST: " + str(r.status_code))

    rsoup = BeautifulSoup(r.text, "html.parser")

    print("Page snippet: " + rsoup.get_text()[300:700].replace("\n"," "))

    found = 0

    for tbl in rsoup.find_all("table"):

        rows = tbl.find_all("tr")

        for row in rows[1:]:

            cells = row.find_all("td")

            if len(cells) >= 2:

                name_text = cells[0].get_text().strip()

                if name_text and len(name_text) > 2:

                    found += 1

                    records.append({

                        "name":     name_text,

                        "address":  cells[1].get_text().strip() if len(cells) > 1 else "",

                        "date":     cells[2].get_text().strip() if len(cells) > 2 else "",

                        "doc_type": term,

                        "county":   "Bartow",

                        "state":    "GA"

                    })

    print("Found: " + str(found))



print("TOTAL: " + str(len(records)))

os.makedirs("dashboard", exist_ok=True)

with open(OUTPUT_FILE, "w") as f:

    json.dump({"fetched_at": datetime.datetime.utcnow().isoformat() + "Z", "county": "Bartow", "state": "GA", "total": len(records), "records": records}, f, indent=2)

print("Saved to " + OUTPUT_FILE)
