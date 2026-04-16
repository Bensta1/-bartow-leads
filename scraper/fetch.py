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

print("GET: " + str(resp.status_code))

soup = BeautifulSoup(resp.text, "html.parser")

vs = soup.find("input", {"name": "__VIEWSTATE"})

vsg = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})

ev = soup.find("input", {"name": "__EVENTVALIDATION"})

viewstate = vs["value"] if vs else ""

viewstate_gen = vsg["value"] if vsg else ""

event_val = ev["value"] if ev else ""

print("Viewstate length: " + str(len(viewstate)))



print("=== ALL INPUTS ===")

for inp in soup.find_all("input"):

    n = inp.get("name", "")

    t = inp.get("type", "text")

    v = inp.get("value", "")[:40]

    if n:

        print("INPUT | type=" + t + " | name=" + n + " | val=" + v)



print("=== ALL SELECTS ===")

for sel in soup.find_all("select"):

    n = sel.get("name", "")

    opts = []

    for o in sel.find_all("option"):

        opts.append(o.get("value","") + "=" + o.get_text().strip())

    print("SELECT | name=" + n + " | options=" + str(opts[:10]))



print("=== ALL FORMS ===")

for form in soup.find_all("form"):

    print("FORM action=" + str(form.get("action","")) + " method=" + str(form.get("method","")))



print("Done - check logs above for field names")

os.makedirs("dashboard", exist_ok=True)

with open(OUTPUT_FILE, "w") as f:

    json.dump({"fetched_at": datetime.datetime.utcnow().isoformat() + "Z", "total": 0, "records": []}, f)

print("Saved placeholder")
