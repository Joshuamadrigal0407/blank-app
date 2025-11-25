import argparse
import csv
import re
import time
from typing import List, Dict, Optional

import requests

# ======================
# CONFIG – EDIT THIS
# ======================

# 👉 Replace this with your real Google Places API key
GOOGLE_API_KEY = "YOUR_GOOGLE_PLACES_API_KEY_HERE"

# How long to wait between Google API calls (seconds)
REQUEST_DELAY_SECONDS = 1.0


class LeadFinder:
    """
    Lead finder that:
      1) Searches businesses via Google Places
      2) Looks up details (address, website, phone)
      3) Scrapes public emails from the website (if any)
      4) Has a stub for owner lookup you can plug into a property data provider
    """

    def __init__(self, google_api_key: str, delay_between_requests: float = 1.0):
        if not google_api_key or google_api_key == "YOUR_GOOGLE_PLACES_API_KEY_HERE":
            raise ValueError(
                "You must set GOOGLE_API_KEY at the top of this file "
                "to your real Google Places API key."
            )
        self.google_api_key = google_api_key
        self.delay = delay_between_requests

    # ---------------------------
    # 1) SEARCH BUSINESSES
    # ---------------------------
    def search_businesses(
        self,
        city: str,
        state: str,
        keyword: str,
        max_results: int = 50,
    ) -> List[Dict]:
        """
        Uses Google Places Text Search to find businesses
        like 'warehouses in San Jose, CA'.
        """
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{keyword} in {city}, {state}",
            "key": self.google_api_key,
        }

        businesses: List[Dict] = []
        while True:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            for result in data.get("results", []):
                businesses.append(
                    {
                        "business_name": result.get("name"),
                        "formatted_address": result.get("formatted_address"),
                        "place_id": result.get("place_id"),
                    }
                )
                if len(businesses) >= max_results:
                    return businesses

            next_token = data.get("next_page_token")
            if not next_token:
                break

            # Google requires a small pause before using next_page_token
            time.sleep(2.0)
            params = {"pagetoken": next_token, "key": self.google_api_key}

        return businesses

    # ---------------------------
    # 2) BUSINESS DETAILS
    # ---------------------------
    def get_details_for_business(self, place_id: str) -> Dict:
        """
        Uses Google Places Details API to get website + phone etc.
        """
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,website,formatted_phone_number",
            "key": self.google_api_key,
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        result = response.json().get("result", {})

        return {
            "business_name": result.get("name"),
            "formatted_address": result.get("formatted_address"),
            "website": result.get("website"),
            "phone": result.get("formatted_phone_number"),
        }

    # ---------------------------
    # 3) FIND EMAILS ON WEBSITE
    # ---------------------------
    def find_emails_on_website(
        self,
        url: Optional[str],
        max_bytes: int = 200_000
    ) -> List[str]:
        """
        Fetches the website HTML and tries to find public email addresses.
        Only uses publicly visible content.
        """
        if not url:
            return []

        # Basic sanity: ensure scheme
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        try:
            resp = requests.get(url, timeout=15)
            text = resp.text[:max_bytes]
        except Exception:
            return []

        # Simple regex for emails
        possible_emails = set(
            re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        )

        # Filter out some obvious junk
        filtered = {
            e
            for e in possible_emails
            if not e.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg"))
        }

        return sorted(filtered)

    # ---------------------------
    # 4) OWNER LOOKUP (STUB)
    # ---------------------------
    def lookup_owner_for_address(self, full_address: str) -> Dict[str, Optional[str]]:
        """
        STUB: This is where you would integrate a property data provider.

        For example, using an API from:
          - PropertyRadar
          - Reonomy
          - PropStream
          - County/assessor API (if available)

        Right now it returns empty values.
        """
        return {
            "owner_name": None,
            "owner_mailing_address": None,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Find business leads with address, owner info, and public emails."
    )
    parser.add_argument("--city", required=True, help="City to search, e.g. 'San Jose'")
    parser.add_argument("--state", required=True, help="State code, e.g. 'CA'")
    parser.add_argument(
        "--keyword",
        required=True,
        help="Type of business, e.g. 'warehouse', 'winery', 'shopping center', etc.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=30,
        help="Max number of businesses to pull from Google Places.",
    )
    parser.add_argument(
        "--output",
        default="leads.csv",
        help="Output CSV file name (default: leads.csv).",
    )

    args = parser.parse_args()

    lf = LeadFinder(
        google_api_key=GOOGLE_API_KEY,
        delay_between_requests=REQUEST_DELAY_SECONDS,
    )

    print(f"Searching for '{args.keyword}' in {args.city}, {args.state}...")
    businesses = lf.search_businesses(
        city=args.city,
        state=args.state,
        keyword=args.keyword,
        max_results=args.max_results,
    )
    print(f"Found {len(businesses)} businesses, fetching details...")

    rows = []
    for idx, b in enumerate(businesses, start=1):
        place_id = b.get("place_id")
        if not place_id:
            continue

        details = lf.get_details_for_business(place_id)
        address = details.get("formatted_address")
        website = details.get("website")

        # Get public emails from website
        emails = lf.find_emails_on_website(website)
        email_list_str = ", ".join(emails) if emails else ""

        # Owner lookup (currently stubbed)
        owner = lf.lookup_owner_for_address(address or "")

        row = {
            "business_name": details.get("business_name"),
            "property_address": address,
            "owner_name": owner.get("owner_name"),
            "owner_mailing_address": owner.get("owner_mailing_address"),
            "website": website,
            "phone": details.get("phone"),
            "emails_found": email_list_str,
        }
        rows.append(row)

        print(
            f"[{idx}/{len(businesses)}] {row['business_name'] or 'Unknown'} "
            f"- {row['property_address'] or 'No address'} "
            f"- Emails: {email_list_str or 'none'}"
        )

        time.sleep(REQUEST_DELAY_SECONDS)

    fieldnames = [
        "business_name",
        "property_address",
        "owner_name",
        "owner_mailing_address",
        "website",
        "phone",
        "emails_found",
    ]

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Saved {len(rows)} leads to {args.output}")


if __name__ == "__main__":
    main()

