#!/usr/bin/env python3

from playwright.sync_api import sync_playwright

import json, datetime, os



OUTPUT_FILE   = "dashboard/records.json"

LOOKBACK_DAYS = 30



def save_results(records, start_date, end_date):

    data = {

        "fetched_at":    datetime.datetime.utcnow().isoformat() + "Z",

        "source":        "Georgia Public Notice / Bartow County",

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



def scrape(start_date, end_date):

    records = []

    BASE = "https://georgiapublicnotice.com"



    with sync_playwright() as p:

        browser = p.chromium.launch(

            headless=True,

            args=["--no-sandbox", "--disable-setuid-sandbox"]

        )

        page = browser.new_context(

            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"

        ).new_page()



        print(f"Loading: {BASE}")

        page.goto(BASE, wait_until="networkidle", timeout=45000)

        page.wait_for_timeout(2000)

        print(f"Title: {page.title()}")



        # Debug all selects and inputs

        for sel in page.query_selector_all("select"):

            name = sel.get_attribute("name") or sel.get_attribute("id") or "?"

            opts = [o.inner_text().strip() for o in sel.query_selector_all("option")]

            print(f"SELECT '{name}': {opts[:10]}")



        for inp in page.query_selector_all("input"):

            name = inp.get_attribute("name") or inp.get_attribute("id") or "?"

            typ  = inp.get_attribute("type") or "text"

            print(f"INPUT '{name}' type={typ}")



        # ── Set County to Bartow ──────────────────────────────────

        county_set = False

        for sel in page.query_selector_all("select"):

            opts_text = sel.inner_text().lower()

            if "bartow" in opts_text:

                sel.select_option(label="Bartow")

                print("✅ County set → Bartow")

                county_set = True

                break



        if
