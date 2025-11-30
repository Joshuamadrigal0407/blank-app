import streamlit as st
import pandas as pd
import os
import uuid
from datetime import date

# ============================================================
# SIMPLE LOGIN CONFIG
# ============================================================
# 👉 Change these to whatever you want
APP_USERNAME = "eci"
APP_PASSWORD = "foam123!"

# ============================================================
# SETTINGS / CONFIG
# ============================================================

DATA_FILE = "sprayfoam_crm.csv"

# Your logo (from ECI Foam Systems site / assets)
LOGO_URL = "https://images.leadconnectorhq.com/image/f_webp/q_80/r_1200/u_https%3A//assets.cdn.filesafe.space/lkH7W8xbGl6pzt92LyGS/media/681428e788b94e7763044d2f.png"

# Brand colors - brighter & easier to read
PRIMARY_COLOR = "#f59e0b"  # bright amber / orange
DARK_HEADER = "#111827"    # slate-900
LIGHT_BG = "#f3f4f6"       # gray-100
CARD_BG = "#ffffff"        # white card
TEXT_COLOR = "#111827"     # near-black
MUTED_TEXT = "#6b7280"     # gray-500
BORDER_COLOR = "#e5e7eb"   # gray-200


# ============================================================
# DATA HELPERS
# ============================================================

def load_data():
    """Load CRM data from CSV, or create an empty DataFrame if it doesn't exist yet."""
    if not os.path.exists(DATA_FILE):
        cols = [
            "id",
            "customer_name",
            "company_name",
            "phone",
            "email",
            "address",
            "city",
            "state",
            "zip_code",
            "lead_source",
            "building_type",
            "service_type",
            "roof_type",
            "square_feet",
            "estimated_value",
            "status",
            "next_follow_up",
            "notes",
        ]
        return pd.DataFrame(columns=cols)

    df = pd.read_csv(DATA_FILE)
    # Make sure there's an ID column for editing
    if "id" not in df.columns:
        df["id"] = [str(uuid.uuid4()) for _ in range(len(df))]
    return df


def save_data(df: pd.DataFrame):
    """Save CRM data back to CSV."""
    df.to_csv(DATA_FILE, index=False)


def new_id():
    """Generate a unique ID for a new record."""
    return str(uuid.uuid4())


# ============================================================
# STREAMLIT PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="ECI Foam Systems CRM",
    page_icon="🧯",
    layout="wide",
)

# Global styling: brighter theme, visible colors, clean cards
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {LIGHT_BG};
            color: {TEXT_COLOR};
        }}
        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }}
        h1, h2, h3, h4 {{
            color: {TEXT_COLOR};
            letter-spacing: 0.03em;
        }}
        .crm-header {{
            background: linear-gradient(135deg, {DARK_HEADER}, #020617);
            border-radius: 1rem;
            padding: 1.25rem 1.5rem;
            display: flex;
            align-items: center;
            gap: 1.25rem;
            box-shadow: 0 14px 35px rgba(15,23,42,0.45);
        }}
        .crm-header-text-main {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #f9fafb;
            margin-bottom: 0.25rem;
        }}
        .crm-header-text-sub {{
            font-size: 0.9rem;
            color: #e5e7eb;
            margin: 0;
        }}
        .crm-header-pill {{
            display: inline-block;
            margin-top: 0.4rem;
            font-size: 0.75rem;
            color: #f9fafb;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            border: 1px solid rgba(249,250,251,0.35);
        }}
        .crm-card {{
            background: {CARD_BG};
            border-radius: 0.9rem;
            padding: 1rem 1.25rem;
            border: 1px solid {BORDER_COLOR};
            box-shadow: 0 12px 28px rgba(148,163,184,0.25);
        }}
        .stat-number {{
            font-size: 1.6rem;
            font-weight: 700;
            color: {TEXT_COLOR};
        }}
        .stat-label {{
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: {MUTED_TEXT};
        }}
        .stat-pill {{
            font-size: 0.75rem;
            padding: 0.1rem 0.5rem;
            border-radius: 999px;
            background: rgba(249,250,251,0.95);
            border: 1px solid {BORDER_COLOR};
            color: {MUTED_TEXT};
        }}
        .dataframe td, .dataframe th {{
            font-size: 0.85rem;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIMPLE LOGIN GATE
# ============================================================

def login_screen():
    st.markdown("## 🔐 Login to ECI Foam Systems CRM")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if username == APP_USERNAME and password == APP_PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Logged in successfully.")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")

# Initialize auth flag
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# If not authenticated, show only login and stop
if not st.session_state["authenticated"]:
    login_screen()
    st.stop()

# Optional: logout button in sidebar
if st.sidebar.button("🚪 Logout"):
    st.session_state["authenticated"] = False
    st.experimental_rerun()


# ============================================================
# HEADER SECTION WITH LOGO (only visible after login)
# ============================================================

header_col1, header_col2 = st.columns([1, 3])

with header_col1:
    st.image(LOGO_URL, caption="ECI Foam Systems", use_column_width=True)

with header_col2:
    st.markdown(
        """
        <div class="crm-header">
            <div style="flex: 1;">
                <div class="crm-header-text-main">ECI Foam Systems CRM</div>
                <p class="crm-header-text-sub">
                    Simple, elite tracking for spray foam roofing, roof coatings, and insulation jobs – 
                    from first call to completed project.
                </p>
                <span class="crm-header-pill">
                    Central & Northern California • Commercial & Industrial Roofing
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")  # spacer


# ============================================================
# LOAD DATA
# ============================================================

df = load_data()

# ============================================================
# STATS ROW
# ============================================================

total_records = len(df)
open_statuses = ["New Lead", "Contacted", "Quoted", "Scheduled", "In Progress"]
open_records = df[df["status"].isin(open_statuses)].shape[0] if not df.empty else 0
completed_records = df[df["status"] == "Completed"].shape[0] if not df.empty else 0
lost_records = df[df["status"] == "Lost"].shape[0] if not df.empty else 0

stat1, stat2, stat3, stat4 = st.columns(4)

with stat1:
    st.markdown(
        f"""
        <div class="crm-card">
            <div class="stat-label">Total Records</div>
            <div class="stat-number">{total_records}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with stat2:
    st.markdown(
        f"""
        <div class="crm-card">
            <div class="stat-label">Open / Active</div>
            <div class="stat-number">{open_records}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with stat3:
    st.markdown(
        f"""
        <div class="crm-card">
            <div class="stat-label">Completed Jobs</div>
            <div class="stat-number">{completed_records}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with stat4:
    st.markdown(
        f"""
        <div class="crm-card">
            <div class="stat-label">Lost Leads</div>
            <div class="stat-number">{lost_records}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")  # spacer


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🔎 Filters")

status_options = ["All"] + sorted([s for s in df["status"].dropna().unique()])
status_filter = st.sidebar.selectbox("Status", status_options)

city_options = ["All"] + sorted([c for c in df["city"].dropna().unique()])
city_filter = st.sidebar.selectbox("City", city_options)

service_options = ["All"] + sorted([s for s in df["service_type"].dropna().unique()])
service_filter = st.sidebar.selectbox("Service Type", service_options)

search_text = st.sidebar.text_input("Search customer / company / address", "")

# Apply filters
filtered = df.copy()

if status_filter != "All":
    filtered = filtered[filtered["status"] == status_filter]

if city_filter != "All":
    filtered = filtered[filtered["city"] == city_filter]

if service_filter != "All":
    filtered = filtered[filtered["service_type"] == service_filter]

if search_text.strip():
    q = search_text.strip().lower()
    mask = (
        filtered["customer_name"].fillna("").str.lower().str.contains(q)
        | filtered["company_name"].fillna("").str.lower().str.contains(q)
        | filtered["address"].fillna("").str.lower().str.contains(q)
    )
    filtered = filtered[mask]


# ============================================================
# TABS (VIEW / ADD / EDIT)
# ============================================================

tab_view, tab_add, tab_edit = st.tabs(
    ["📋 Customers & Leads", "➕ Add Customer / Lead", "✏️ Edit Customer / Lead"]
)

# ------------------------------------------------------------
# TAB 1: VIEW
# ------------------------------------------------------------

with tab_view:
    st.subheader(f"Customers & Leads ({len(filtered)})")

    display_cols = [
        "customer_name",
        "company_name",
        "phone",
        "email",
        "address",
        "city",
        "state",
        "square_feet",
        "service_type",
        "status",
        "estimated_value",
        "next_follow_up",
        "lead_source",
    ]
    existing_cols = [c for c in display_cols if c in filtered.columns]

    st.markdown('<div class="crm-card">', unsafe_allow_html=True)
    st.dataframe(filtered[existing_cols], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.download_button(
        label="📥 Download filtered as CSV",
        data=filtered.to_csv(index=False),
        file_name="sprayfoam_crm_filtered.csv",
        mime="text/csv",
    )


# ------------------------------------------------------------
# TAB 2: ADD CUSTOMER / LEAD
# ------------------------------------------------------------

with tab_add:
    st.subheader("Add Customer / Lead")

    with st.form("add_lead_form"):
        # CUSTOMER INFO
        st.markdown("#### 👤 Customer Information")
        c1, c2 = st.columns(2)

        with c1:
            customer_name = st.text_input("Customer Name *")
            company_name = st.text_input("Company Name (optional)")
            phone = st.text_input("Phone")
            email = st.text_input("Email")

        with c2:
            address = st.text_input("Job / Property Address")
            city = st.text_input("City")
            state_val = st.text_input("State", value="CA")
            zip_code = st.text_input("ZIP Code")

        # JOB INFO
        st.markdown("#### 🏗 Job / Spray Foam Details")
        c3, c4 = st.columns(2)

        with c3:
            lead_source = st.selectbox(
                "Lead Source",
                ["", "Referral", "Google", "Website", "Facebook", "Cold Call", "Repeat Customer", "Other"],
            )
            building_type = st.selectbox(
                "Building Type",
                ["", "Commercial", "Industrial", "Residential", "Agricultural", "Other"],
            )
            service_type = st.selectbox(
                "Service Type",
                [
                    "",
                    "Spray Foam Roof",
                    "Foam + Coating",
                    "Roof Coating Only",
                    "Interior Spray Foam",
                    "Wall Insulation",
                    "Other",
                ],
            )

        with c4:
            roof_type = st.selectbox(
                "Roof Type",
                ["", "Flat", "Metal", "TPO/PVC", "Shingle", "Tile", "Other"],
            )
            square_feet = st.text_input("Approx. Square Feet (roof/area)")
            estimated_value = st.text_input("Estimated Job Value ($)")
            status = st.selectbox(
                "Status",
                [
                    "New Lead",
                    "Contacted",
                    "Quoted",
                    "Scheduled",
                    "In Progress",
                    "Completed",
                    "Lost",
                    "Existing Customer",
                ],
            )
            next_follow_up = st.date_input(
                "Next Follow-Up Date",
                value=date.today(),
            )

        notes = st.text_area("Notes (scope, conditions, objections, etc.)")

        submitted = st.form_submit_button("💾 Save")

    if submitted:
        if not customer_name.strip() and not company_name.strip():
            st.error("Please enter at least a customer name or company name.")
        else:
            new_row = {
                "id": new_id(),
                "customer_name": customer_name.strip(),
                "company_name": company_name.strip(),
                "phone": phone.strip(),
                "email": email.strip(),
                "address": address.strip(),
                "city": city.strip(),
                "state": state_val.strip(),
                "zip_code": zip_code.strip(),
                "lead_source": lead_source.strip(),
                "building_type": building_type.strip(),
                "service_type": service_type.strip(),
                "roof_type": roof_type.strip(),
                "square_feet": square_feet.strip(),
                "estimated_value": estimated_value.strip(),
                "status": status.strip(),
                "next_follow_up": str(next_follow_up),
                "notes": notes,
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Customer / lead saved.")
            st.experimental_rerun()


# ------------------------------------------------------------
# TAB 3: EDIT CUSTOMER / LEAD
# ------------------------------------------------------------

with tab_edit:
    st.subheader("Edit Customer / Lead")

    if df.empty:
        st.info("No records to edit yet. Add some first.")
    else:
        # Create a label to make it easy to find the right record
        df["label"] = (
            df["customer_name"].fillna("")
            + " | "
            + df["company_name"].fillna("")
            + " | "
            + df["address"].fillna("")
        )

        selected_label = st.selectbox("Select a record to edit", df["label"].tolist())
        selected_row = df[df["label"] == selected_label].iloc[0]
        selected_idx = df[df["label"] == selected_label].index[0]

        with st.form("edit_lead_form"):
            st.markdown("#### 👤 Customer Information")
            c1, c2 = st.columns(2)

            with c1:
                customer_name_e = st.text_input(
                    "Customer Name", value=selected_row.get("customer_name", "")
                )
                company_name_e = st.text_input(
                    "Company Name", value=selected_row.get("company_name", "")
                )
                phone_e = st.text_input(
                    "Phone", value=selected_row.get("phone", "")
                )
                email_e = st.text_input(
                    "Email", value=selected_row.get("email", "")
                )

            with c2:
                address_e = st.text_input(
                    "Job / Property Address", value=selected_row.get("address", "")
                )
                city_e = st.text_input("City", value=selected_row.get("city", ""))
                state_e = st.text_input(
                    "State", value=selected_row.get("state", "CA")
                )
                zip_code_e = st.text_input(
                    "ZIP Code", value=selected_row.get("zip_code", "")
                )

            st.markdown("#### 🏗 Job / Spray Foam Details")
            c3, c4 = st.columns(2)

            with c3:
                lead_source_e = st.text_input(
                    "Lead Source", value=selected_row.get("lead_source", "")
                )
                building_type_e = st.selectbox(
                    "Building Type",
                    ["", "Commercial", "Industrial", "Residential", "Agricultural", "Other"],
                    index=["", "Commercial", "Industrial", "Residential", "Agricultural", "Other"].index(
                        selected_row.get("building_type", "")
                    )
                    if selected_row.get("building_type", "") in
                    ["", "Commercial", "Industrial", "Residential", "Agricultural", "Other"]
                    else 0,
                )
                service_type_e = st.selectbox(
                    "Service Type",
                    [
                        "",
                        "Spray Foam Roof",
                        "Foam + Coating",
                        "Roof Coating Only",
                        "Interior Spray Foam",
                        "Wall Insulation",
                        "Other",
                    ],
                    index=[
                        "",
                        "Spray Foam Roof",
                        "Foam + Coating",
                        "Roof Coating Only",
                        "Interior Spray Foam",
                        "Wall Insulation",
                        "Other",
                    ].index(selected_row.get("service_type", ""))
                    if selected_row.get("service_type", "") in
                    [
                        "",
                        "Spray Foam Roof",
                        "Foam + Coating",
                        "Roof Coating Only",
                        "Interior Spray Foam",
                        "Wall Insulation",
                        "Other",
                    ]
                    else 0,
                )

            with c4:
                roof_type_e = st.selectbox(
                    "Roof Type",
                    ["", "Flat", "Metal", "TPO/PVC", "Shingle", "Tile", "Other"],
                    index=["", "Flat", "Metal", "TPO/PVC", "Shingle", "Tile", "Other"].index(
                        selected_row.get("roof_type", "")
                    )
                    if selected_row.get("roof_type", "") in
                    ["", "Flat", "Metal", "TPO/PVC", "Shingle", "Tile", "Other"]
                    else 0,
                )
                square_feet_e = st.text_input(
                    "Approx. Square Feet", value=str(selected_row.get("square_feet", ""))
                )
                estimated_value_e = st.text_input(
                    "Estimated Job Value ($)",
                    value=str(selected_row.get("estimated_value", "")),
                )
                status_e = st.selectbox(
                    "Status",
                    [
                        "New Lead",
                        "Contacted",
                        "Quoted",
                        "Scheduled",
                        "In Progress",
                        "Completed",
                        "Lost",
                        "Existing Customer",
                    ],
                    index=[
                        "New Lead",
                        "Contacted",
                        "Quoted",
                        "Scheduled",
                        "In Progress",
                        "Completed",
                        "Lost",
                        "Existing Customer",
                    ].index(selected_row.get("status", "New Lead"))
                    if selected_row.get("status", "New Lead") in
                    [
                        "New Lead",
                        "Contacted",
                        "Quoted",
                        "Scheduled",
                        "In Progress",
                        "Completed",
                        "Lost",
                        "Existing Customer",
                    ]
                    else 0,
                )
                next_follow_up_e = st.date_input(
                    "Next Follow-Up Date",
                    value=pd.to_datetime(
                        selected_row.get("next_follow_up", date.today())
                    ).date(),
                )

            notes_e = st.text_area(
                "Notes", value=selected_row.get("notes", "")
            )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                update_btn = st.form_submit_button("💾 Update")
            with col_btn2:
                delete_btn = st.form_submit_button("🗑️ Delete")

        if update_btn:
            df.at[selected_idx, "customer_name"] = customer_name_e
            df.at[selected_idx, "company_name"] = company_name_e
            df.at[selected_idx, "phone"] = phone_e
            df.at[selected_idx, "email"] = email_e
            df.at[selected_idx, "address"] = address_e
            df.at[selected_idx, "city"] = city_e
            df.at[selected_idx, "state"] = state_e
            df.at[selected_idx, "zip_code"] = zip_code_e
            df.at[selected_idx, "lead_source"] = lead_source_e
            df.at[selected_idx, "building_type"] = building_type_e
            df.at[selected_idx, "service_type"] = service_type_e
            df.at[selected_idx, "roof_type"] = roof_type_e
            df.at[selected_idx, "square_feet"] = square_feet_e
            df.at[selected_idx, "estimated_value"] = estimated_value_e
            df.at[selected_idx, "status"] = status_e
            df.at[selected_idx, "next_follow_up"] = str(next_follow_up_e)
            df.at[selected_idx, "notes"] = notes_e

            df = df.drop(columns=["label"], errors="ignore")
            save_data(df)
            st.success("Customer / lead updated.")
            st.experimental_rerun()

        if delete_btn:
            df = df.drop(index=selected_idx)
            df = df.drop(columns=["label"], errors="ignore")
            df.reset_index(drop=True, inplace=True)
            save_data(df)
            st.success("Customer / lead deleted.")
            st.experimental_rerun()
