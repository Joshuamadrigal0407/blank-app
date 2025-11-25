import streamlit as st
import requests
import csv
import time

# ======================================================
#                 CONFIGURATION
# ======================================================

# 👉 Put your property data provider API key here
API_KEY = "YOUR_API_KEY_HERE"

# 👉 Put your property provider base URL here
# (Example placeholder. Replace with real one from Reonomy / PropStream / PropertyRadar, etc.)
PROPERTY_API_URL = "https://api.yourprovider.com/v1/search"

# 👉 Maximum number of properties to pull
MAX_RESULTS = 100

# 👉 Output file
OUTPUT_FILE = "commercial_properties_ca.csv"


# ======================================================
#                 FUNCTIONS
# ======================================================

def query_properties(city: str, state: str = "CA") -> list:
    """
    Queries a legitimate property data provider for commercial/industrial properties.
    You MUST replace fields based on your provider's API documentation.
    """

    params = {
        "city": city,
        "state": state,
        "property_type": "commercial,industrial",  # Many APIs accept comma-separated types
        "api_key": API_KEY,
        "limit": MAX_RESULTS
    }

    try:
        response = requests.get(PROPERTY_API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        return data.get("results", [])

    except Exception as e:
        print(f"[ERROR] Could not query API: {e}")
        return []


def extract_fields(record: dict) -> dict:
    """
    Extracts useful fields from the API response.
    You MUST adapt key names based on your provider's documentation.
    """
    owner = record.get("owner", {})
    contact = record.get("contact", {})
    prop = record.get("property", {})

    return {
        "property_address": prop.get("address"),
        "property_city": prop.get("city"),
        "property_state": prop.get("state"),
        "property_zip": prop.get("zip"),
        "owner_name": owner.get("name"),
        "owner_mailing_address": owner.get("mailing_address"),
        "owner_email": contact.get("email"),
        "owner_phone": contact.get("phone")
    }


def save_to_csv(rows: list, filename: str):
    if not rows:
        print("No data to save.")
        return

    keys = rows[0].keys()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} properties to {filename}")


# ======================================================
#                    MAIN PROGRAM
# ======================================================

def main():
    print("=== California Commercial Property Lead Generator ===")
    print("This software pulls owner names, emails, addresses, and property info")
    print("from a legitimate property database API.\n")

    city = input("Enter a California city (example: Fresno): ").strip()

    print(f"\nSearching commercial + industrial properties in {city}, CA...\n")

    results = query_properties(city)
    extracted = []

    for idx, r in enumerate(results, start=1):
        row = extract_fields(r)
        extracted.append(row)

        print(f"[{idx}/{len(results)}] {row.get('property_address')} "
              f"- Owner: {row.get('owner_name')} "
              f"- Email: {row.get('owner_email')}")

        time.sleep(0.5)

    save_to_csv(extracted, OUTPUT_FILE)


if __name__ == "__main__":
    main()

