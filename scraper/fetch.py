#!/usr/bin/env python3

from playwright.sync_api import sync_playwright

import json, datetime, os



OUTPUT_FILE   = "dashboard/records.json"

LOOKBACK_DAYS = 30



def save_results(records, start_date, end_date):

    data = {

        "fetched_at":    datetime.datetime.utcnow().isoformat() + "Z",

        "source":        "Bartow County GA / GSCCCA",

        "county":        "Bartow", "state": "GA",

        "date_range":    {"start": str(start_date), "end": str(end_date)},

        "lookback_days": LOOKBACK_DAYS,

        "total":         len(records),

        "with_address":  sum(1 for r in records if r.get("address")),

        "records":       records

    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:

        json.dump(data, f, indent=2)

    print(f"✅ Saved {len(records)} records → {OUTPUT_FILE}")



def scrape_gsccca(start_date, end_date):

    records = []

    URL = "https://search.gsccca.org/RealEstate/"



    with sync_playwright() as p:

        browser = p.chromium.launch(

            headless=True,

            args=["--no-sandbox", "--disable-setuid-sandbox"]

        )

        context = browser.new_context(

            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"

        )

        page = context.new_page()



        print(f"Loading: {URL}")

        try:

            page.goto(URL, wait_until="networkidle", timeout=30000)

        except Exception as e:

            print(f"⚠️ networkidle timeout ({e}), continuing anyway...")



        print(f"Title: {page.title()}")



        # Debug: list all form elements

        all_els = page.query_selector_all("input, select, textarea")

        print(f"Form elements found: {len(all_els)}")

        for el in all_els:

            tag  = el.evaluate("e => e.tagName")

            name = el.get_attribute("name") or el.get_attribute("id") or "(none)"

            print(f"  {tag}: {name}")



        for doc_code, doc_label in [("NFS","Notice of Foreclosure Sale"),

                                     ("LIS","Lis Pendens"),

                                     ("FIFA","Fi Fa / Lien")]:

            try:

                print(f"\n── Searching: {doc_label} ──")



                # Select Bartow County

                for sel in page.query_selector_all("select"):

                    opts = sel.inner_text().lower()

                    if "bartow" in opts:

                        sel.select_option(label="Bartow")

                        print("  ✅ County → Bartow")

                        break



                # Select doc type

                for sel in page.query_selector_all("select"):

                    opts = sel.inner_text().lower()

                    if "foreclosure" in opts or "lis pendens" in opts or "fi fa" in opts:

                        try:

                            sel.select_option(label=doc_label)

                        except:

                            sel.select_option(value=doc_code)

                        print(f"  ✅ Doc type → {doc_label}")

                        break



                # Fill date range

                for inp in page.query_selector_all("input"):

                    name = (inp.get_attribute("name") or inp.get_attribute("id") or "").lower()

                    if any(x in name for x in ["fromdate","from_date","startdate","datefrom"]):

                        inp.fill(start_date.strftime("%m/%d/%Y"))

                        print(f"  ✅ From: {start_date}")

                    elif any(x in name for x in ["todate","to_date","enddate","dateto"]):

                        inp.fill(end_date.strftime("%m/%d/%Y"))

                        print(f"  ✅ To:   {end_date}")



                # Click Search

                btn = (page.query_selector("input[value='Search']") or

                       page.query_selector("button:has-text('Search')") or

                       page.query_selector("input[type='submit']"))

                if not btn:

                    print("  ❌ No search button found!")

                    continue

                btn.click()

                try:

                    page.wait_for_load_state("networkidle", timeout=30000)

                except:

                    page.wait_for_timeout(3000)

                print("  ✅ Search submitted")



                # Parse results table

                found = 0

                for tbl in page.query_selector_all("table"):

                    for row in tbl.query_selector_all("tr")[1:]:

                        cells = row.query_selector_all("td")

                        if len(cells) >= 2:

                            name = cells[0].inner_text().strip()

                            if name and len(name) > 2:

                                found += 1

                                records.append({

                                    "name":        name,

                                    "address":     cells[1].inner_text().strip() if len(cells)>1 else "",

                                    "case_number": cells[2].inner_text().strip() if len(cells)>2 else "",

                                    "date":        cells[3].inner_text().strip() if len(cells)>3 else "",

                                    "doc_type":    doc_label,

                                })

                print(f"  → {found} records found")



                # Return to search page for next doc type

                page.goto(URL, wait_until="networkidle", timeout=30000)



            except Exception as e:

                import traceback

                print(f"  ERROR: {e}")

                traceback.print_exc()



        browser.close()

    return records



def main():

    end_date   = datetime.date.today()

    start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)

    print(f"Bartow County GA leads: {start_date} → {end_date}")

    records = scrape_gsccca(start_date, end_date)

    print(f"\nTotal records: {len(records)}")

    save_results(records, start_date, end_date)



if __name__ == "__main__":

    main()
