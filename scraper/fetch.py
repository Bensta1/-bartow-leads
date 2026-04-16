import json, datetime, os, requests

from bs4 import BeautifulSoup



OUTPUT_FILE = "dashboard/records.json"

LOOKBACK_DAYS = 30

end_date = datetime.date.today()

start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)

print("Running: " + str(start_date) + " to " + str(end_date))

records = []

session = requests.Session()

session.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"})

resp = session.get("https://georgiapublicnotice.com", timeout=20)

print("GET status: " + str(resp.status_code))

soup = BeautifulSoup(resp.text, "html.parser")

vs = soup.find("input", {"name": "__VIEWSTATE"})

vsg = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})

ev = soup.find("input", {"name": "__EVENTVALIDATION"})

viewstate = vs["value"] if vs else ""

viewstate_gen = vsg["value"] if vsg else ""

event_val = ev["value"] if ev else ""

print("Viewstate length: " + str(len(viewstate)))

print("--- ALL INPUT NAMES ---")

for inp in soup.find_all("input"):

    n = inp.get("name", "")

    v = inp.get("value", "")

    t = inp.get("type", "")

    if n:

        print("  " + t + " | " + n + " | val=" + v[:30])

print("--- ALL SELECT NAMES ---")

for sel in soup.find_all("select"):

    n = sel.get("name", "")

    opts = [o.get("value","") + "=" + o.get_text().strip() for o in sel.find_all("option")]

    print("  " + n + ": " + str(opts[:15]))

BTN    = "ctl100$ContentPlaceHolder1$as1$btnTool"

TXT    = "ctl100$ContentPlaceHolder1$as1$txtSearch"

COUNTY = "ctl100$ContentPlaceHolder1$as1$lstCounty7"

DDL    = "ctl100$ContentPlaceHolder1$as1$ddlPopularSearches"

for category in ["Debtors and Creditors", "Condemnations"]:

    print("--- Category: " + category + " ---")

    post_data = {

        "__VIEWSTATE": viewstate,

        "__VIEWSTATEGENERATOR": viewstate_gen,

        "__EVENTVALIDATION": event_val,

        "__LASTFOCUS": "",

        "__EVENTTARGET": "",

        "__EVENTARGUMENT": "",

        DDL: category,

        COUNTY: "on",

        BTN: "Search"

    }

    r = session.post("https://georgiapublicnotice.com", data=post_data, timeout=20)

    print("POST status: " + str(r.status_code))

    rsoup = BeautifulSoup(r.text, "html.parser")

    body = rsoup.get_text()

    print("Response snippet: " + body[200:800])

    found = 0

    for tbl in rsoup.find_all("table"):

        rows = tbl.find_all("tr")

        if len(rows) < 2:

            continue

        for row in rows[1:]:

            cells = row.find_all("td")

            if len(cells) >= 2:

                name_text = cells[0].get_text().strip()

                if name_text and len(name_text) > 2:

                    found += 1

                    records.append({"name": name_text, "address": cells[1].get_text().strip() if len(cells) > 1 else "", "date": cells[2].get_text().strip() if len(cells) > 2 else "", "doc_type": category, "county": "Bartow", "state": "GA"})

    print("Found: " + str(found))

print("TOTAL: " + str(len(records)))

os.makedirs("dashboard", exist_ok=True)

data = {"fetched_at": datetime.datetime.utcnow().isoformat() + "Z", "source": "Georgia Public Notice", "county": "Bartow", "state": "GA", "date_range": {"start": str(start_date), "end": str(end_date)}, "lookback_days": LOOKBACK_DAYS, "total": len(records), "with_address": sum(1 for r in records if r.get("address")), "records": records}

with open(OUTPUT_FILE, "w") as f:

    json.dump(data, f, indent=2)

print("Saved to " + OUTPUT_FILE)
