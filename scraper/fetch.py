#!/usr/bin/env python3

import requests

from bs4 import BeautifulSoup

import json, datetime, os, traceback



OUTPUT_FILE  = "dashboard/records.json"

LOOKBACK_DAYS = 30



HEADERS = {

    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",

    "Accept":        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

    "Accept-Language": "en-US,en;q=0.9",

    "Referer":       "https://search.gsccca.org/",

}



# ── Correct URLs to try ────────────────────────────────────────────

GSCCCA_URLS = [

    "https://search.gsccca.org/RealEstate/",

    "https://search.gsccca.org/UCC/",

]



def save_results(records, start_date, end_date):

    data = {

        "fetched_at":   datetime.datetime.utcnow().isoformat() + "Z",

        "source":       "Bartow County GA / GSCCCA",

        "county":       "Bartow",

        "state":        "GA",

        "date_range":   {"start": str(start_date), "end": str(end_date)},

        "lookback_days": LOOKBACK_DAYS,

        "total":        len(records),

        "with_address": sum(1 for r in records if r.get("address")),

        "records":      records

    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:

        json.dump(data, f, indent=2)

    print(f"✅ Saved {len(records)} records → {OUTPUT_FILE}")



def probe_gsccca(session, start_date, end_date):

    """Try GSCCCA main real-estate search."""

    records = []

    BASE    = "https://search.gsccca.org/RealEstate/"



    # ── 1. Hit the landing page to grab cookies & form fields ──────

    print(f"\n[GSCCCA] Loading: {BASE}")

    try:

        r0 = session.get(BASE, timeout=20)

        print(f"  Status: {r0.status_code}  |  {len(r0.text)} chars")

        if r0.status_code != 200:

            print("  ❌ Bad status — dumping first 300 chars:")

            print(r0.text[:300])

            return records

    except Exception as e:

        print(f"  ❌ Connection error: {e}")

        return records



    soup = BeautifulSoup(r0.text, "html.parser")



    # Debug all fields

    inputs  = [(i.get("name"), i.get("value","")[:30]) for i in soup.find_all("input")  if i.get("name")]

    selects = [(s.get("name"), [o.get_text(strip=True) for o in s.find_all("option")][:5]) for s in soup.find_all("select") if s.get("name")]

    print(f"  INPUTS:  {inputs}")

    print(f"  SELECTS: {selects}")



    # ── 2. Find county select & Bartow value ──────────────────────

    county_name = county_value = None

    for sel in soup.find_all("select"):

        for opt in sel.find_all("option"):

            if "bartow" in opt.get_text(strip=True).lower():

                county_name  = sel.get("name")

                county_value = opt.get("value")

                print(f"  ✅ Bartow: field='{county_name}' value='{county_value}'")

                break



    if not county_name:

        print("  ⚠️  No county dropdown found — page structure may need JS")

        # Print the raw HTML so we can see what's there

        print("  HTML snippet:", r0.text[500:1000])

        return records



    # ── 3. Collect hidden ASP.NET fields ──────────────────────────

    form_data = {}

    for inp in soup.find_all("input"):

        n = inp.get("name")

        v = inp.get("value", "")

        if n:

            form_data[n] = v



    # ── 4. Search each doc type ───────────────────────────────────

    doc_types = [

        ("NFS",  "Notice of Foreclosure Sale"),

        ("LIS",  "Lis Pendens"),

        ("FIFA", "Fi Fa / Lien"),

    ]



    for doc_code, doc_label in doc_types:

        try:

            print(f"\n  Searching {doc_label}...")



            # Update form data with our search values

            search_data = form_data.copy()

            search_data[county_name] = county_value



            # Try to find and set doc type & date fields

            for key in list(search_data.keys()):

                kl = key.lower()

                if "doctype" in kl or "documenttype" in kl:

                    search_data[key] = doc_code

                if "fromdate" in kl or "startdate" in kl or "datefrom" in kl:

                    search_data[key] = start_date.strftime("%m/%d/%Y")

                if "todate" in kl or "enddate" in kl or "dateto" in kl:

                    search_data[key] = end_date.strftime("%m/%d/%Y")

                if "btnsearch" in kl or "search" in kl.replace("_",""):

                    search_data[key] = "Search"



            r2 = session.post(BASE, data=search_data, timeout=30)

            print(f"  Response: {r2.status_code}  |  {len(r2.text)} chars")



            s2      = BeautifulSoup(r2.text, "html.parser")

            pg_text = s2.get_text(" ").lower()

            print(f"  Snippet: {pg_text[200:450]}")



            found = 0

            for tbl in s2.find_all("table"):

                for row in tbl.find_all("tr")[1:]:

                    cells = row.find_all("td")

                    if len(cells) >= 2:

                        name = cells[0].get_text(strip=True)

                        if name and len(name) > 3:

                            found += 1

                            records.append({

                                "name":        name,

                                "address":     cells[1].get_text(strip=True) if len(cells)>1 else "",

                                "case_number": cells[2].get_text(strip=True) if len(cells)>2 else "",

                                "date":        cells[3].get_text(strip=True) if len(cells)>3 else "",

                                "doc_type":    doc_label,

                            })

            print(f"  → {found} records parsed")



        except Exception as e:

            print(f"  ERROR: {e}")

            traceback.print_exc()



    return records



def main():

    end_date   = datetime.date.today()

    start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)

    print(f"Bartow County GA leads: {start_date} → {end_date}")



    session = requests.Session()

    session.headers.update(HEADERS)



    records = probe_gsccca(session, start_date, end_date)

    print(f"\nTotal records: {len(records)}")

    save_results(records, start_date, end_date)



if __name__ == "__main__":

    main()
