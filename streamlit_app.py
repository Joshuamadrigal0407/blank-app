import csv
import re
import urllib.request
import urllib.error
import os
import time
from typing import List

INPUT_FILE = "businesses.csv"
OUTPUT_FILE = "businesses_with_emails.csv"


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def find_emails_on_url(url: str, max_bytes: int = 200_000) -> List[str]:
    url = normalize_url(url)
    if not url:
        return []

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            content_bytes = resp.read(max_bytes)

        try:
            text = content_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text = content_bytes.decode("latin-1", errors="ignore")
    except Exception as e:
        print(f"  ! Could not fetch {url} ({e})")
        return []

    # Simple regex for emails
    possible_emails = set(
        re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    )

    # Filter out obvious junk (image filenames etc.)
    filtered = {
        e
        for e in possible_emails
        if not e.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg"))
    }

    return sorted(filtered)


def main():
    # If no input file yet, create a template for you to fill
    if not os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "address", "website"])
            writer.writerow(["Sample Business", "123 Main St, YourCity, CA", "https://example.com"])

        print(f"Created {INPUT_FILE}.")
        print("Open it in Excel, add your businesses (name, address, website), then run this script again.")
        return

    # Read existing businesses
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(f"No data rows found in {INPUT_FILE}. Add some businesses first.")
        return

    print(f"Found {len(rows)} businesses in {INPUT_FILE}")
    output_rows = []
    total = len(rows)

    for idx, row in enumerate(rows, start=1):
        name = row.get("name", "").strip()
        addr = row.get("address", "").strip()
        website = row.get("website", "").strip()

        print(f"[{idx}/{total}] {name or '(no name)'} - {website or 'no website'}")

        emails = find_emails_on_url(website) if website else []
        email_str = ", ".join(emails)

        out_row = dict(row)
        out_row["emails_found"] = email_str
        output_rows.append(out_row)

        # Small delay to be polite to websites
        time.sleep(1)

    fieldnames = list(rows[0].keys())
    if "emails_found" not in fieldnames:
        fieldnames.append("emails_found")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Done. Wrote results with emails to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
