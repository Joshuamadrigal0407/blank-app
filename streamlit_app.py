import streamlit as st
import pandas as pd
import re
import urllib.request
import urllib.error
import time

st.set_page_config(page_title="Commercial Property Lead Scraper", layout="wide")

# -----------------------------
# Utility functions
# -----------------------------

def normalize_url(url):
    """Ensure URL has http/https."""
    if not isinstance(url, str):
        return ""
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def find_emails_on_url(url, max_bytes=200000):
    """Scrape a website and extract visible email addresses."""
    emails = set()
    url = normalize_url(url)
    if not url:
        return []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_bytes = resp.read(max_bytes)

        try:
            text = content_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text = content_bytes.decode("latin-1", errors="ignore")

    except Exception as e:
        st.write(f"❌ Could not fetch {url} ({e})")
        return []

    # Regex for emails
    possible = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    for e in possible:
        if not e.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
            emails.add(e)

    return sorted(emails)


# -----------------------------
# Streamlit UI
# -----------------------------

st.title("🏭 Commercial & Industrial Property Lead Scraper")
st.write("Upload a CSV of properties and I will extract public emails from the websites.")
st.write("No API keys required. 100% plug-and-play.")

sample_csv = """
name,address,website
ABC Industrial,123 Main St Fresno CA,https://example.com
XYZ Warehouse,456 Commerce Bakersfield CA,https://warehouse.com
"""

st.subheader("📥 Step 1: Upload Your CSV")
uploaded = st.file_uploader("Upload a CSV with columns: name, address, website", type=["csv"])

st.write("Example CSV format:")
st.code(sample_csv, language="csv")

if uploaded:
    df = pd.read_csv(uploaded)
    
    # Make sure required columns exist
    required_cols = {"name", "address", "website"}
    if not required_cols.issubset(df.columns.str.lower()):
        st.error("CSV must contain columns: name, address, website")
    else:
        st.success("CSV uploaded successfully!")

        if st.button("🔍 Scrape Emails Now"):

            st.subheader("🔎 Scanning Websites for Emails...")
            results = []

            progress = st.progress(0)
            total = len(df)

            for idx, row in df.iterrows():
                name = row.get("name")
                address = row.get("address")
                website = row.get("website")

                st.write(f"**[{idx+1}/{total}] Checking:** {name} — {website}")

                emails = find_emails_on_url(website)
                email_str = ", ".join(emails)

                results.append({
                    "name": name,
                    "address": address,
                    "website": website,
                    "emails_found": email_str
                })

                progress.progress((idx+1) / total)
                time.sleep(0.5)

            st.success("Done! Emails extracted.")

            result_df = pd.DataFrame(results)

            st.subheader("📄 Results")
            st.dataframe(result_df, use_container_width=True)

            # Download button
            st.download_button(
                label="📥 Download Results as CSV",
                data=result_df.to_csv(index=False),
                file_name="leads_with_emails.csv",
                mime="text/csv"
            )

