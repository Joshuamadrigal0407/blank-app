import csv
import re
import urllib.request
import urllib.error
import time

OUTPUT_FILE = "leads_with_emails.csv"


def normalize_url(url):
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def find_emails_on_url(url, max_bytes=200000):
    emails = set()
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
        print("  ! Could not fetch {} ({})".format(url, e))
        return []

    # Simple regex for emails
    for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        e_low = e.lower()
        # Filter out obvious junk (image filenames etc.)
        if not e_low.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
            emails.add(e)

    return sorted(emails)


def main():
    print("Lead Email Finder (no API keys, plug-and-play)")
    print("------------------------------------------------")
    print("You will be asked to enter business info.")
    print("When you're done, just press ENTER on 'Business name' to finish.\n")

    leads = []

    while True:
        name = input("Business name (or press ENTER to finish): ").strip()
        if not name:
            break
        address = input("Business address (optional): ").strip()
        website = input("Website (e.g. example.com or https://example.com): ").strip()
        print("")
        leads.append({"name": name, "address": address, "website": website})

    if not leads:
        print("No businesses entered. Exiting.")
        return

    print("\nSearching for emails on each website...\n")

    output_rows = []
    total = len(leads)

    for idx, lead in enumerate(leads, start=1):
        name = lead["name"]
        address = lead["address"]
        website = lead["website"]

        print("[{}/{}] {} - {}".format(idx, total, name or "(no name)", website or "no website"))

        emails = find_emails_on_url(website) if website else []
        email_str = ", ".join(emails)

        print("   Emails found: {}".format(email_str or "none"))
        print("")

        output_rows.append(
            {
                "name": name,
                "address": address,
                "website": website,
                "emails_found": email_str,
            }
        )

        # Small delay to be polite to websites
        time.sleep(1)

    fieldnames = ["name", "address", "website", "emails_found"]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print("Done.")
    print("Results saved in '{}' (you can open this in Excel).".format(OUTPUT_FILE))


if __name__ == "__main__":
    main()

