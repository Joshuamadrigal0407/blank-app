import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mini PropertyRadar - Owner Lookup", layout="wide")

st.title("🏠 Mini PropertyRadar – Property Owner Lookup")
st.write(
    "Upload a CSV of properties (from PropertyRadar, county data, or your own list) "
    "and filter/search to get owner names, addresses, and emails."
)

st.markdown("""
**Expected columns (or similar):**
- owner_name / owner / owner_full_name  
- owner_mailing_address / mailing_address  
- property_address / situs_address / address  
- city  
- county  
- property_type / land_use  
- owner_email / email  
""")

uploaded_file = st.file_uploader("📥 Upload your property CSV", type=["csv"])


def pick_column(possible_names, columns_lower_to_original):
    """
    Try to find the best matching column from a list of possible names.
    Returns the original column name or None.
    """
    for name in possible_names:
        if name in columns_lower_to_original:
            return columns_lower_to_original[name]
    return None


if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception:
        st.error("Could not read CSV. Make sure it's a standard comma-separated file.")
        st.stop()

    st.success(f"Loaded {len(df)} rows from CSV.")

    # Map lowercase column names to original names
    cols_lower_map = {c.lower().strip(): c for c in df.columns}

    # Try to detect key columns
    owner_col = pick_column(
        ["owner_name", "owner", "owner full name", "owner_full_name"],
        cols_lower_map,
    )
    owner_mail_col = pick_column(
        ["owner_mailing_address", "mailing_address", "mailing address"],
        cols_lower_map,
    )
    prop_addr_col = pick_column(
        ["property_address", "situs_address", "address", "site_address"],
        cols_lower_map,
    )
    city_col = pick_column(["city", "prop_city", "property_city"], cols_lower_map)
    county_col = pick_column(["county", "prop_county"], cols_lower_map)
    prop_type_col = pick_column(
        ["property_type", "land_use", "use_code", "prop_type"],
        cols_lower_map,
    )
    email_col = pick_column(["owner_email", "email", "contact_email"], cols_lower_map)

    # Show what we found
    st.subheader("🔍 Column Detection")
    st.write("**Owner name column:**", owner_col or "❌ Not found")
    st.write("**Owner mailing address column:**", owner_mail_col or "❌ Not found")
    st.write("**Property address column:**", prop_addr_col or "❌ Not found")
    st.write("**City column:**", city_col or "❌ Not found")
    st.write("**County column:**", county_col or "❌ Not found")
    st.write("**Property type / land use column:**", prop_type_col or "❌ Not found")
    st.write("**Owner email column:**", email_col or "❌ Not found")

    st.info(
        "If any important column says ❌ Not found, rename your column in Excel to something like "
        "`owner_name`, `property_address`, `owner_email`, then re-upload."
    )

    # Sidebar filters
    st.sidebar.header("🔎 Filters")

    mask = pd.Series(True, index=df.index)

    # Filter by county
    if county_col is not None:
        counties = sorted(df[county_col].dropna().astype(str).unique())
        selected_counties = st.sidebar.multiselect(
            "County", counties, default=counties
        )
        mask &= df[county_col].astype(str).isin(selected_counties)

    # Filter by city
    if city_col is not None:
        cities = sorted(df[city_col].dropna().astype(str).unique())
        selected_cities = st.sidebar.multiselect(
            "City", cities, default=cities
        )
        mask &= df[city_col].astype(str).isin(selected_cities)

    # Filter by property type
    if prop_type_col is not None:
        prop_types = sorted(df[prop_type_col].dropna().astype(str).unique())
        selected_types = st.sidebar.multiselect(
            "Property Type / Land Use", prop_types, default=prop_types
        )
        mask &= df[prop_type_col].astype(str).isin(selected_types)

    # Simple text search (owner or address)
    text_query = st.sidebar.text_input(
        "Search (owner or address contains):", ""
    ).strip()

    def contains_text(series, query):
        return series.astype(str).str.contains(query, case=False, na=False)

    if text_query:
        text_mask = pd.Series(False, index=df.index)
        if owner_col is not None:
            text_mask |= contains_text(df[owner_col], text_query)
        if prop_addr_col is not None:
            text_mask |= contains_text(df[prop_addr_col], text_query)
        mask &= text_mask

    # Apply mask
    filtered = df[mask].copy()

    st.subheader(f"📋 Filtered Properties ({len(filtered)} rows)")

    # Build a nice simplified table for display
    display_cols = []
    label_map = {}

    if owner_col is not None:
        display_cols.append(owner_col)
        label_map[owner_col] = "Owner Name"
    if owner_mail_col is not None:
        display_cols.append(owner_mail_col)
        label_map[owner_mail_col] = "Owner Mailing Address"
    if prop_addr_col is not None:
        display_cols.append(prop_addr_col)
        label_map[prop_addr_col] = "Property Address"
    if city_col is not None:
        display_cols.append(city_col)
        label_map[city_col] = "City"
    if county_col is not None:
        display_cols.append(county_col)
        label_map[county_col] = "County"
    if prop_type_col is not None:
        display_cols.append(prop_type_col)
        label_map[prop_type_col] = "Property Type / Land Use"
    if email_col is not None:
        display_cols.append(email_col)
        label_map[email_col] = "Owner Email"

    if display_cols:
        to_show = filtered[display_cols].rename(columns=label_map)
    else:
        st.warning("No core columns detected; showing raw data.")
        to_show = filtered

    st.dataframe(to_show, use_container_width=True)

    # Download filtered results
    st.subheader("📥 Download Filtered List")
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download as CSV",
        data=csv_bytes,
        file_name="filtered_property_owners.csv",
        mime="text/csv",
    )
else:
    st.info("Upload a CSV to get started.")

