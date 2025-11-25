import argparse
import csv
import re
import time
from typing import List, Dict, Optional

import requests

# ======================
# CONFIG – EDIT THIS
# ======================

# Put your real Google Places API key here
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

        businesses = []
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

