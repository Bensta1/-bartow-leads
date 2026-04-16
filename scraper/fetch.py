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

print("Status: " + str(resp.status_code))

soup = BeautifulSoup(resp.text, "html.parser")

vs = soup.find("input", {"name": "__VIEWSTATE"})

vsg = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})

ev = soup.find("input", {"name": "__EVENTVALIDATION"})

viewstate = vs["value"] if vs else ""

viewstate_gen = vsg["value"] if vsg else ""

event_val = ev["value"] if ev else ""

print("Viewstate OK: " + str(len(viewstate) > 0))

btn_name = ""

txt_name = ""

county_name = ""

for inp in soup.find_all("input"):

    n = inp.get("name", "")

    if "btnTool" in n:

        btn_name = n

    if "txtSearch" in n:

        txt_name = n

    if "lstCounty7" in n:

        county_name = n

print("btn=" + btn_name)

print("txt=" + txt_name)

print("county=" + county_name)

for term in ["foreclosure", "lis pendens", "tax lien"]:

    print("Searching: " + term)

    post_data = {

        "__VIEWSTATE": viewstate,

        "__VIEWSTATEGENERATOR": viewstate_gen,

        "__EVENTVALIDATION": event_val,

        "__LASTFOCUS": "",

        txt_name: term,

        county_name: "on",

        btn_name: "Search"

    }

    r = session.post("https://georgiapublicnotice.com", data=post_data, timeout=20)

    print("Post status: " + str(r.status_code))

    rsoup = BeautifulSoup(r.text, "html.parser")

    print(rsoup.get_text()[:500])

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

                    records.append({"name": name_text, "address": cells[1].get_text().strip() if len(cells) > 1 else "", "date": cells[2].get_text().strip() if len(cells) > 2 else "", "doc_type": term, "county": "Bartow", "state": "GA"})

    print("Found: " + str(found))

print("TOTAL: " + str(len(records)))

os.makedirs("dashboard", exist_ok=True)

data = {"fetched_at": datetime.datetime.utcnow().isoformat() + "Z", "source": "Georgia Public Notice", "county": "Bartow", "state": "GA", "date_range": {"start": str(start_date), "end": str(end_date)}, "lookback_days": LOOKBACK_DAYS, "total": len(records), "with_address": sum(1 for r in records if r.get("address")), "records": records}

with open(OUTPUT_FILE, "w") as f:

    json.dump(data, f, indent=2)

print("Saved to " + OUTPUT_FILE)
