import argparse
import csv
import re
import time
from typing import List, Dict, Optional, Set

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
        Looks up the property owner using a 3rd-party property data API.

        You MUST customize:
          - PROPERTY_API_BASE_URL
          - query params / JSON parsing
        based on your provider's API documentation.
        """
        from urllib.parse import urlencode

        if not full_address:
            return {
                "owner_name": None,
                "owner_mailing_address": None,
            }

        # Make sure you set PROPERTY_API_KEY and PROPERTY_API_BASE_URL at the top.
        if not PROPERTY_API_KEY or PROPERTY_API_KEY == "YOUR_PROPERTY_API_KEY_HERE":
            # If you haven't set it yet, just skip owner lookup
            return {
                "owner_name": None,
                "owner_mailing_address": None,
            }

        try:
            # ⚠️ THIS IS A TEMPLATE – you MUST adjust the parameters
            # to match your provider's docs.
            #
            # Common patterns:
            #   - GET /v1/property?address=123+Main+St,+San+Jose,+CA
            #   - Or POST with JSON body
            query_params = {
                "address": full_address,
                "api_key": PROPERTY_API_KEY,  # or use headers if required
            }
            url = f"{PROPERTY_API_BASE_URL}?{urlencode(query_params)}"

            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # ⚠️ Adjust this based on the provider's JSON response.
            # Example of a typical structure:
            # {
            #   "results": [
            #       {
            #           "owner": {
            #               "name": "ABC Investments LLC",
            #               "mailing_address": "PO Box 123, San Jose, CA 95112"
            #           }
            #       }
            #   ]
            # }
            results = data.get("results", [])
            if not results:
                return {
                    "owner_name": None,
                    "owner_mailing_address": None,
                }

            first = results[0]
            owner_info = first.get("owner", {})

            owner_name = owner_info.get("name")
            owner_mailing_address = owner_info.get("mailing_address")

            return {
                "owner_name": owner_name,
                "owner_mailing_address": owner_mailing_address,
            }

        except Exception as e:
            # If anything goes wrong, just return empty fields so the rest of
            # the script still works.
            print(f"Owner lookup failed for address '{full_address}': {e}")
            return {
                "owner_name": None,
                "owner_mailing_address": None,
            }


def build_commercial_keywords() -> List[str]:
    """
    Returns a list of keywords that tend to match commercial / industrial properties.
    """
    return [
        "commercial building",
        "commercial property",
        "industrial building",
        "industrial park",
        "warehouse",
        "distribution center",
        "logistics center",
        "manufacturing",
        "business park",
        "office building",
        "shopping center",
        "strip mall",
    ]


def dedupe_by_place_id(business_lists: List[List[Dict]]) -> List[Dict]:
    """
    Merge multiple business lists together and remove duplicates
    based on Google place_id.
    """
    seen: Set[str] = set()
    merged: List[Dict] = []

    for blist in business_lists:
        for b in blist:
            pid = b.get("place_id")
            if not pid:
                continue
            if pid in seen:
                continue
            seen.add(pid)
            merged.append(b)

    return merged


def main():
    parser = argparse.ArgumentParser(
        description="Find commercial business leads with address, optional owner info, and public emails."
    )
    parser.add_argument("--city", required=True, help="City to search, e.g. 'San Jose'")
    parser.add_argument(
        "--state",
        default="CA",
        help="State code, default 'CA' (California).",
    )
    parser.add_argument(
        "--keyword",
        help="Custom keyword, e.g. 'winery', 'warehouse', etc. "
             "If you pass this, only this keyword is used.",
    )
    parser.add_argument(
        "--commercial",
        action="store_true",
        help="If set, searches a bundle of commercial-building keywords (warehouses, industrial, offices, etc.)",
    )
    parser.add_argument(
        "--max-per-keyword",
        type=int,
        default=30,
        help="Max number of businesses to pull from Google Places per keyword.",
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

    # Decide which keywords to use
    keywords: List[str]
    if args.keyword:
        keywords = [args.keyword]
        print(f"Using custom keyword: {args.keyword!r}")
    elif args.commercial:
        keywords = build_commercial_keywords()
        print("Using commercial keyword bundle:")
        for kw in keywords:
            print(f"  - {kw}")
    else:
        # Default if nothing specified: generic commercial building
        keywords = ["commercial building"]
        print("No keyword or --commercial given. Using default keyword: 'commercial building'")

    all_business_lists: List[List[Dict]] = []

    # 1) SEARCH FOR EACH KEYWORD
    for kw in keywords:
        print(f"\nSearching for '{kw}' in {args.city}, {args.state}...")
        businesses = lf.search_businesses(
            city=args.city,
            state=args.state,
            keyword=kw,
            max_results=args.max_per_keyword,
        )
        print(f"  Found {len(businesses)} results for keyword '{kw}'")
        all_business_lists.append(businesses)
        # Small pause between keyword batches
        time.sleep(1.0)

    # Merge & dedupe by place_id
    merged_businesses = dedupe_by_place_id(all_business_lists)
    print(f"\nTotal unique businesses after merging/deduping: {len(merged_businesses)}")

    rows = []
    total = len(merged_businesses)
    for idx, b in enumerate(merged_businesses, start=1):
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
            f"[{idx}/{total}] {row['business_name'] or 'Unknown'} "
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

