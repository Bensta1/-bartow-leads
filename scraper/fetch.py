#!/usr/bin/env python3

from playwright.sync_api import sync_playwright

import json, datetime, os, base64



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



    with sync_playwright() as p:

        browser = p.chromium.launch(

            headless=True,

            args=["--no-sandbox", "--disable-setuid-sandbox"]

        )

        context = browser.new_context(

            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"

        )

        page = context.new_page()



        # ── Try direct search URL with GET parameters ──────────────

        # Bartow County code = 8 in GSCCCA

        for doc_code, doc_label in [

            ("NFS",  "Notice of Foreclosure Sale"),

            ("LIS",  "Lis Pendens"),

            ("FIFA", "Fi Fa / Lien"),

        ]:

            try:

                url = (

                    f"https://search.gsccca.org/RealEstate/instrumentindex.aspx"

                    f"?county=8"

                    f"&doctype={doc_code}"

                    f"&fromdate={start_date.strftime('%m/%d/%Y')}"

                    f"&todate={end_date.strftime('%m/%d/%Y')}"

                    f"&appid=2"

                )

                print(f"\n── {doc_label} ──")

                print(f"URL: {url}")



                page.goto(url, wait_until="networkidle", timeout=45000)

                page.wait_for_timeout(3000)  # extra wait for JS



                title = page.title()

                print(f"Title: {title}")



                # Check for selects NOW (after JS loads)

                selects = page.query_selector_all("select")

                print(f"Selects found: {len(selects)}")

                for sel in selects:

                    name = sel.get_attribute("name") or sel.get_attribute("id")

                    opts = [o.inner_text().strip() for o in sel.query_selector_all("option")][:8]

                    print(f"  SELECT {name}: {opts}")



                # Save screenshot as base64 for debugging

                screenshot = page.screenshot()

                b64 = base64.b64encode(screenshot).decode()

                print(f"SCREENSHOT_B64_START_{doc_code}")

                print(b64[:200])  # First 200 chars to confirm it works

                print(f"SCREENSHOT_B64_END_{doc_code}")



                # Print HTML snippet of main content

                body = page.inner_text("body")

                print(f"Body text (first 500): {body[:500]}")



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

                                records.append({

                                    "name":        name_text,

                                    "address":     cells[1].inner_text().strip() if len(cells)>1 else "",

                                    "case_number": cells[2].inner_text().strip() if len(cells)>2 else "",

                                    "date":        cells[3].inner_text().strip() if len(cells)>3 else "",

                                    "doc_type":    doc_label,

                                })

                print(f"→ {found} records found")



            except Exception as e:

                import traceback

                print(f"ERROR: {e}")

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
