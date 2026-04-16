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
        print("Loading georgiapublicnotice.com")
        page.goto("https://georgiapublicnotice.com", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(3000)
        print("Title: " + page.title())
        selects = page.query_selector_all("select")
        print("Selects found: " + str(len(selects)))
        for s in selects:
            name = s.get_attribute("name") or s.get_attribute("id") or "unknown"
            opts = [o.inner_text().strip() for o in s.query_selector_all("option")]
            print("SELECT " + name + ": " + str(opts[:10]))
        inputs = page.query_selector_all("input")
        print("Inputs found: " + str(len(inputs)))
        for i in inputs:
            name = i.get_attribute("name") or i.get_attribute("id") or "unknown"
            itype = i.get_attribute("type") or "text"
            print("INPUT " + name + " type=" + itype)
        body = page.inner_text("body")
        print("Page text:")
        print(body[:1000])
        browser.close()
    os.makedirs("dashboard", exist_ok=True)
    data = {
        "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",
        "source": "Georgia Public Notice",
        "county": "Bartow",
        "state": "GA",
        "date_range": {"start": str(start_date), "end": str(end_date)},
        "lookback_days": LOOKBACK_DAYS,
        "total": len(records),
        "with_address": 0,
        "records": records
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("Saved " + str(len(records)) + " records")

main()