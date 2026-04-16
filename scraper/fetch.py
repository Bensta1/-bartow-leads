#!/usr/bin/env python3

import json

import datetime

import os

from playwright.sync_api import sync_playwright



OUTPUT_FILE = "dashboard/records.json"

LOOKBACK_DAYS = 30



def main():

    end_date = datetime.date.today()

    start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)

    print("Bartow County GA leads: " + str(start_date) + " to " + str(end_date))

    records = []



    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])

        page = browser.new_page()



        search_terms = ["foreclosure", "lis pendens", "lien"]



        for term in search_terms:

            print("--- Searching: " + term + " ---")

            page.goto("https://georgiapublicnotice.com", wait_until="networkidle", timeout=45000)

            page.wait_for_timeout(3000)



            # Check Bartow county checkbox (index 7)

            try:

                bartow = page.query_selector("input[id*='lstCounty7']")

                if not bartow:

                    bartow = page.query_selector("input[name*='lstCounty7']")

                if bartow:

                    bartow.check()

                    print("Bartow county checked")

                else:

                    print("WARNING: Bartow checkbox not found")

            except Exception as e:

                print("Checkbox error: " + str(e))



            # Type search term

            try:

                txt = page.query_selector("input[name*='txtSearch']")

                if not txt:

                    txt = page.query_selector("input[id*='txtSearch']")

                if txt:

                    txt.fill(term)

                    print("Search term entered: " + term)

            except Exception as e:

                print("Search input error: " + str(e))



            # Set date range if date fields exist

            try:

                for inp in page.query_selector_all("input[type='text']"):

                    name = inp.get_attribute("name") or inp.get_attribute("id") or ""

                    if "from" in name.lower() or "start" in name.lower() or "begin" in name.lower():

                        inp.fill(start_date.strftime("%m/%d/%Y"))

                        print("From date set: " + str(start_date))

                    elif "to" in name.lower() or "end" in name.lower():

                        inp.fill(end_date.strftime("%m/%d/%Y"))

                        print("To date set: " + str(end_date))

            except Exception as e:

                print("Date error: " + str(e))



            # Click search button

            try:

                btn = page.query_selector("input[name*='btnTool']")

                if not btn:

                    btn = page.query_selector("input[id*='btnTool']")

                if not btn:

                    btn = page.query_selector("input[type='submit']")

                if btn:

                    btn.click()

                    page.wait_for_timeout(5000)

                    print("Search submitted")

                else:

                    print("No button found")

                    continue

            except Exception as e:

                print("Button error: " + str(e))

                continue



            # Print results page info

            print("Results title: " + page.title())

            body_text = page.inner_text("body")

            print("Results snippet: " + body_text[:800])



            # Parse results table

            found = 0

            for tbl in page.query_selector_all("table"):

                rows = tbl.query_selector_all("tr")

                if len(rows) < 2:

                    continue

                for row in rows[1:]:

                    cells = row.query_selector_all("td")

                    if len(cells) >= 2:

                        name_text = cells[0].inner_text().strip()

                        if name_text and len(name_text) > 2:

                            found += 1

                            rec = {

                                "name": name_text,

                                "address": cells[1].inner_text().strip() if len(cells) > 1 else "",

                                "case_number": cells[2].inner_text().strip() if len(cells) > 2 else "",

                                "date": cells[3].inner_text().strip() if len(cells) > 3 else "",

                                "doc_type": term,

                                "county": "Bartow",

                                "state": "GA"

                            }

                            records.append(rec)



            # Also try divs/articles if no table

            if found == 0:

                for item in page.query_selector_all(".notice, .result, .listing, article, .notice-item"):

                    text = item.inner_text().strip()

                    if text and len(text) > 10:

                        found += 1

                        records.append({

                            "name": text[:100],

                            "address": "",

                            "case_number": "",

                            "date": "",

                            "doc_type": term,

                            "county": "Bartow",

                            "state": "GA"

                        })



            print("Found " + str(found) + " records for: " + term)



        browser.close()



    print("TOTAL RECORDS: " + str(len(records)))

    os.makedirs("dashboard", exist_ok=True)

    data = {

        "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",

        "source": "Georgia Public Notice",

        "county": "Bartow",

        "state": "GA",

        "date_range": {"start": str(start_date), "end": str(end_date)},

        "lookback_days": LOOKBACK_DAYS,

        "total": len(records),

        "with_address": sum(1 for r in records if r.get("address")),

        "records": records

    }

    with open(OUTPUT_FILE, "w") as f:

        json.dump(data, f, indent=2)

    print("Saved to " + OUTPUT_FILE)



main()