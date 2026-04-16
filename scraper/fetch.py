#!/usr/bin/env python3

"""

Bartow County GA Leads Scraper

Fetches foreclosure notices from GSCCCA

"""



import requests

from bs4 import BeautifulSoup

import json

import datetime

import os

import sys

import re



OUTPUT_FILE = "dashboard/records.json"

LOOKBACK_DAYS = 7



HEADERS = {

    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

    "Accept-Language": "en-US,en;q=0.5",

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

    print(f"Saved {len(records)} records to {OUTPUT_FILE}")



def fetch_gsccca(start_date, end_date):

    session = requests.Session()

    session.headers.update(HEADERS)

    records = []



    search_url = "https://search.gsccca.org/RealEstate/"

    doc_types = [

        ("NFS", "Notice of Foreclosure Sale"),

        ("LIS", "Lis Pendens"),

    ]



    # Find Bartow County ID from dropdown

    bartow_id = "8"

    try:

        r = session.get(search_url, timeout=15)

        soup = BeautifulSoup(r.text, "html.parser")

        county_select = soup.find("select", {"name": re.compile(r"county", re.I)})

        if county_select:

            for option in county_select.find_all("option"):

                if "bartow" in option.text.lower():

                    bartow_id = option.get("value")

                    print(f"Found Bartow County ID: {bartow_id}")

                    break

    except Exception as e:

        print(f"Warning: using fallback county ID=8 ({e})")



    for doc_code, doc_name in doc_types:

        try:

            print(f"Searching: {doc_name}...")

            params = {

                "county_id": bartow_id,

                "doc_type": doc_code,

                "start_date": start_date.strftime("%m/%d/%Y"),

                "end_date": end_date.strftime("%m/%d/%Y"),

            }

            response = session.get(search_url, params=params, timeout=30)

            print(f"  Status: {response.status_code}")

            soup = BeautifulSoup(response.text, "html.parser")



            for table in soup.find_all("table"):

                rows = table.find_all("tr")

                for row in rows[1:]:

                    cells = row.find_all(["td"])

                    if len(cells) >= 3:

                        name = cells[0].get_text(strip=True)

                        if name and name.lower() not in ["name", "grantor", "grantee", ""]:

                            records.append({

                                "name": name,

                                "address": cells[1].get_text(strip=True) if len(cells) > 1 else "",

                                "case_number": cells[2].get_text(strip=True) if len(cells) > 2 else "",

                                "date": cells[3].get_text(strip=True) if len(cells) > 3 else "",

                                "doc_type": doc_name,

                            })

        except Exception as e:

            print(f"  Error: {e}")



    return records



def main():

    end_date = datetime.date.today()

    start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)

    print(f"Fetching Bartow County leads: {start_date} to {end_date}")



    records = fetch_gsccca(start_date, end_date)

    print(f"Total records: {len(records)}")

    save_results(records, start_date, end_date)



if __name__ == "__main__":

    main()
