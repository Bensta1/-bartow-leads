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

        page.goto("https://georgiapublicnotice.com", wait_until="networkidle", timeout=45000)

        page.wait_for_timeout(3000)

        print("Title: " + page.title())



        # Find and print ALL county checkboxes and their labels

        print("--- COUNTY CHECKBOXES ---")

        boxes = page.query_selector_all("input[type='checkbox']")

        for box in boxes:

            name = box.get_attribute("name") or box.get_attribute("id") or ""

            val = box.get_attribute("value") or ""

            if "County" in name or "county" in name:

                # Try to find associated label

                bid = box.get_attribute("id") or ""

                label = ""

                if bid:

                    lbl = page.query_selector("label[for='" + bid + "']")

                    if lbl:

                        label = lbl.inner_text().strip()

                print("COUNTY: name=" + name + " value=" + val + " label=" + label)



        # Print ALL dropdown options for Popular Searches

        print("--- SEARCH CATEGORIES ---")

        for s in page.query_selector_all("select"):

            name = s.get_attribute("name") or s.get_attribute("id") or "unknown"

            opts = [o.inner_text().strip() for o in s.query_selector_all("option")]

            print("SELECT " + name + ": " + str(opts))



        # Print radio button options

        print("--- RADIO BUTTONS ---")

        for r in page.query_selector_all("input[type='radio']"):

            name = r.get_attribute("name") or ""

            val = r.get_attribute("value") or ""

            rid = r.get_attribute("id") or ""

            label = ""

            if rid:

                lbl = page.query_selector("label[for='" + rid + "']")

                if lbl:

                    label = lbl.inner_text().strip()

            print("RADIO name=" + name + " value=" + val + " label=" + label)



        # Print date inputs specifically

        print("--- DATE INPUTS ---")

        for i in page.query_selector_all("input"):

            name = i.get_attribute("name") or i.get_attribute("id") or ""

            itype = i.get_attribute("type") or "text"

            if any(x in name.lower() for x in ["date","from","to","start","end"]):

                print("DATE INPUT: " + name + " type=" + itype)



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