#!/usr/bin/env python3

import requests

from bs4 import BeautifulSoup

import json, datetime, os, traceback



OUTPUT_FILE = "dashboard/records.json"

LOOKBACK_DAYS = 30  # extended to 30 days to catch more records



HEADERS = {

    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",

    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

    "Accept-Language": "en-US,en;q=0.9",

}



def save_results(records, start_date, end_date):

    data = {

        "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",

        "source": "Bartow County GA Clerk / GSCCCA",

        "county": "Bartow",

        "state": "GA",

        "date_range": {"start": str(start_date), "end": str(end_date)},

        "lookback_days": LOOKBACK_DAYS,

        "total": len(records),

        "with_address": sum(1 for r in records if r.get("address")),

        "records": records

    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:

        json.dump(data, f, indent=2)

    print(f"✅ Saved {len(records)} records to {OUTPUT_FILE}")



def fetch_gsccca(start_date, end_date):

    session = requests.Session()

    session.headers.update(HEADERS)

    records = []

    SEARCH_URL = "https://search.gsccca.org/RealEstate/index.aspx"



    # ── Step 1: Load the form page ──────────────────────────────

    print("Loading GSCCCA search page...")

    try:

        r = session.get(SEARCH_URL, timeout=20)

        print(f"  Page status: {r.status_code}  |  Length: {len(r.text)} chars")

    except Exception as e:

        print(f"  FAILED to load page: {e}")

        return records



    soup = BeautifulSoup(r.text, "html.parser")



    # ── Debug: print ALL form input/select names ─────────────────

    all_inputs  = [i.get("name") for i in soup.find_all("input")  if i.get("name")]

    all_selects = [s.get("name") for s in soup.find_all("select") if s.get("name")]

    print(f"  INPUT  fields: {all_inputs}")

    print(f"  SELECT fields: {all_selects}")



    # ── Find Bartow County value ──────────────────────────────────

    bartow_value      = "8"   # fallback

    county_field_name = None

    for sel in soup.find_all("select"):

        for opt in sel.find_all("option"):

            if "bartow" in opt.get_text(strip=True).lower():

                bartow_value      = opt.get("value", "8")

                county_field_name = sel.get("name")

                print(f"  Bartow → field={county_field_name}, value={bartow_value}")

                break



    # ── Hidden ASP.NET fields ─────────────────────────────────────

    vs  = soup.find("input", {"name": "__VIEWSTATE"})

    ev  = soup.find("input", {"name": "__EVENTVALIDATION"})

    vsg = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})



    # ── Step 2: Search each doc type ─────────────────────────────

    for doc_code, doc_label in [("NFS","Notice of Foreclosure Sale"),

                                  ("LIS","Lis Pendens"),

                                  ("FIFA","Fi Fa / Lien")]:

        try:

            print(f"\nSearching: {doc_label} ({doc_code})...")



            post_data = {

                "__VIEWSTATE":          vs["value"]  if vs  else "",

                "__EVENTVALIDATION":    ev["value"]  if ev  else "",

                "__VIEWSTATEGENERATOR": vsg["value"] if vsg else "",

                # Try both common ASP.NET naming patterns

                "ctl00$cphBody$ddlCounty":              bartow_value,

                "ctl00$ContentPlaceHolder1$ddlCounty":  bartow_value,

                "ctl00$cphBody$ddlDocType":             doc_code,

                "ctl00$ContentPlaceHolder1$ddlDocType": doc_code,

                "ctl00$cphBody$txtFromDate":            start_date.strftime("%m/%d/%Y"),

                "ctl00$ContentPlaceHolder1$txtFromDate":start_date.strftime("%m/%d/%Y"),

                "ctl00$cphBody$txtToDate":              end_date.strftime("%m/%d/%Y"),

                "ctl00$ContentPlaceHolder1$txtToDate":  end_date.strftime("%m/%d/%Y"),

                "ctl00$cphBody$btnSearch":              "Search",

                "ctl00$ContentPlaceHolder1$btnSearch":  "Search",

            }



            # Override with the real field name if we found it

            if county_field_name:

                post_data[county_field_name] = bartow_value



            r2 = session.post(SEARCH_URL, data=post_data, timeout=30)

            print(f"  Response: {r2.status_code}  |  {len(r2.text)} chars")



            soup2   = BeautifulSoup(r2.text, "html.parser")

            pg_text = soup2.get_text(separator=" ").lower()



            # Debug snippet

            print(f"  Page text sample: {pg_text[300:550]}")



            if "no record" in pg_text or "0 record" in pg_text:

                print(f"  → Site says no records for {doc_code}")

                continue



            found = 0

            for table in soup2.find_all("table"):

                for row in table.find_all("tr")[1:]:   # skip header

                    cells = row.find_all("td")

                    if len(cells) >= 2:

                        name = cells[0].get_text(strip=True)

                        if name and len(name) > 3:

                            found += 1

                            records.append({

                                "name":        name,

                                "address":     cells[1].get_text(strip=True) if len(cells) > 1 else "",

                                "case_number": cells[2].get_text(strip=True) if len(cells) > 2 else "",

                                "date":        cells[3].get_text(strip=True) if len(cells) > 3 else "",

                                "doc_type":    doc_label,

                            })

            print(f"  → Parsed {found} records")



        except Exception as e:

            print(f"  ERROR: {e}")

            traceback.print_exc()



    return records



def main():

    end_date   = datetime.date.today()

    start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)

    print(f"Bartow County GA leads: {start_date} → {end_date}")

    records = fetch_gsccca(start_date, end_date)

    print(f"\nTotal records: {len(records)}")

    save_results(records, start_date, end_date)



if __name__ == "__main__":

    main()
