import streamlit as st
import pandas as pd
import os
import uuid
from datetime import date, timedelta
import hashlib
import smtplib
import ssl
from email.message import EmailMessage
import calendar  # used for month view calendar

# ============================================================
# SETTINGS / CONFIG
# ============================================================

DATA_FILE = "sprayfoam_crm.csv"
USERS_FILE = "users.csv"           # for login/sign-up accounts
CAL_NOTES_FILE = "calendar_notes.csv"  # for free-form calendar notes

# Your logo
LOGO_URL = (
    "https://images.leadconnectorhq.com/image/f_webp/q_80/r_1200/"
    "u_https%3A//assets.cdn.filesafe.space/lkH7W8xbGl6pzt92LyGS/media/681428e788b94e7763044d2f.png"
)

# Brighter, high-contrast colors (light / clean theme)
PRIMARY_COLOR = "#2563eb"   # blue
ACCENT_COLOR = "#f97316"    # orange
APP_BG = "#f3f4f6"          # light gray background
CARD_BG = "#ffffff"         # white cards
TEXT_COLOR = "#111827"      # near-black
MUTED_TEXT = "#6b7280"      # gray-500
BORDER_COLOR = "#e5e7eb"    # gray-200
HEADER_GRADIENT_LEFT = "#1f2933"
HEADER_GRADIENT_RIGHT = "#111827"

# Choice lists (edit once, used everywhere)
STATUS_CHOICES = [
    "New Lead",
    "Contacted",
    "Quoted",
    "Scheduled",
    "In Progress",
    "Completed",
    "Lost",
    "Existing Customer",
]
BUILDING_TYPES = ["Commercial", "Industrial", "Residential", "Agricultural", "Other"]
SERVICE_TYPES = [
    "Spray Foam Roof",
    "Foam + Coating",
    "Roof Coating Only",
    "Interior Spray Foam",
    "Wall Insulation",
    "Other",
]
ROOF_TYPES = ["Flat", "Metal", "TPO/PVC", "Shingle", "Tile", "Other"]

# ============================================================
# USER / AUTH HELPERS
# ============================================================

def hash_password(password: str) -> str:
    """Return SHA256 hash of a password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users() -> pd.DataFrame:
    """Load users from CSV or create empty."""
    if not os.path.exists(USERS_FILE):
        return pd.DataFrame(columns=["email", "password_hash"])
    df = pd.read_csv(USERS_FILE)
    if "email" not in df.columns or "password_hash" not in df.columns:
        df = pd.DataFrame(columns=["email", "password_hash"])
    return df


def save_users(df: pd.DataFrame):
    """Save users back to CSV."""
    df.to_csv(USERS_FILE, index=False)


def user_exists(email: str) -> bool:
    df = load_users()
    return not df[df["email"].str.lower() == email.lower()].empty


def create_user(email: str, password: str):
    df = load_users()
    new_row = {
        "email": email.strip(),
        "password_hash": hash_password(password.strip()),
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_users(df)


def verify_user(email: str, password: str) -> bool:
    df = load_users()
    if df.empty:
        return False
    row = df[df["email"].str.lower() == email.lower()]
    if row.empty:
        return False
    stored_hash = row.iloc[0]["password_hash"]
    return stored_hash == hash_password(password)


# ============================================================
# DATA HELPERS (CRM)
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
# CALENDAR NOTES HELPERS
# ============================================================

def load_calendar_notes() -> pd.DataFrame:
    """Load calendar notes from CSV (one row per date)."""
    if not os.path.exists(CAL_NOTES_FILE):
        return pd.DataFrame(columns=["date", "note"])
    df = pd.read_csv(CAL_NOTES_FILE)
    if "date" not in df.columns or "note" not in df.columns:
        df = pd.DataFrame(columns=["date", "note"])
    return df


def save_calendar_notes(df: pd.DataFrame):
    """Save calendar notes back to CSV."""
    df.to_csv(CAL_NOTES_FILE, index=False)


# ============================================================
# EMAIL / YAHOO MAIL SENDER
# ============================================================

def send_yahoo_email(from_email: str, app_password: str, to_email: str, subject: str, body: str):
    """Send an email using Yahoo SMTP."""
    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.mail.yahoo.com", 465, context=context) as server:
        server.login(from_email, app_password)
        server.send_message(msg)


# ============================================================
# STREAMLIT PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="ECI Foam Systems CRM",
    page_icon="🧯",
    layout="wide",
)

# Global styling: bright, clear, easy to read
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {APP_BG};
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
            background: linear-gradient(135deg, {HEADER_GRADIENT_LEFT}, {HEADER_GRADIENT_RIGHT});
            border-radius: 1.1rem;
            padding: 1.25rem 1.5rem;
            display: flex;
            align-items: center;
            gap: 1.25rem;
            box-shadow: 0 12px 30px rgba(15,23,42,0.5);
            border: 1px solid rgba(148,163,184,0.4);
        }}
        .crm-header-text-main {{
            font-size: 1.6rem;
            font-weight: 750;
            color: #f9fafb;
            margin-bottom: 0.2rem;
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
            color: #e5e7eb;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            border: 1px solid rgba(248,250,252,0.6);
            background: rgba(37,99,235,0.2);
        }}
        .crm-card {{
            background: {CARD_BG};
            border-radius: 0.9rem;
            padding: 1rem 1.25rem;
            border: 1px solid {BORDER_COLOR};
            box-shadow: 0 8px 22px rgba(148,163,184,0.35);
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
        .dataframe td, .dataframe th {{
            font-size: 0.85rem;
            color: {TEXT_COLOR};
        }}
        .auth-card {{
            background: {CARD_BG};
            border-radius: 1rem;
            padding: 1.5rem 1.75rem;
            border: 1px solid {BORDER_COLOR};
            box-shadow: 0 10px 25px rgba(148,163,184,0.5);
        }}
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: #e5e7eb;
            border-right: 1px solid #d1d5db;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# AUTH / LOGIN + SIGNUP
# ============================================================

def auth_screen():
    logo_col, _ = st.columns([1, 3])
    with logo_col:
        st.image(LOGO_URL, use_column_width=True)

    st.markdown(
        f"""
        <div style="margin-top: 0.5rem; margin-bottom: 1rem;">
            <h2 style="margin-bottom: 0.25rem; color:{TEXT_COLOR};">ECI Foam Systems CRM</h2>
            <p style="color:{MUTED_TEXT}; font-size:0.9rem; margin:0;">
                Secure login • Customer management • Calendar & reminders • Built-in email
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    tab_login, tab_signup = st.tabs(["Login", "Create Account"])

    # LOGIN TAB
    with tab_login:
        st.markdown("#### Login")
        with st.form("login_form"):
            login_email = st.text_input("Email")
            login_password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")

        if submit_login:
            if verify_user(login_email, login_password):
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = login_email
                st.success("Logged in successfully.")
                st.experimental_rerun()
            else:
                st.error("Invalid email or password.")

    # SIGNUP TAB
    with tab_signup:
        st.markdown("#### Create Account")
        with st.form("signup_form"):
            signup_email = st.text_input("Email (this will be your login)")
            signup_password = st.text_input("Password", type="password")
            signup_password2 = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Create Account")

        if submit_signup:
            if not signup_email or not signup_password:
                st.error("Email and password are required.")
            elif signup_password != signup_password2:
                st.error("Passwords do not match.")
            elif user_exists(signup_email):
                st.error("An account with that email already exists.")
            else:
                create_user(signup_email, signup_password)
                st.success("Account created. You can now log in on the Login tab.")
    st.markdown("</div>", unsafe_allow_html=True)


# Init auth state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

# If not logged in, show auth screen
if not st.session_state["authenticated"]:
    auth_screen()
    st.stop()

# ============================================================
# SIDEBAR (only after login)
# ============================================================

st.sidebar.image(LOGO_URL, use_column_width=True)
st.sidebar.markdown(
    f"""
    <div style="margin-bottom:0.75rem;">
        <p style="font-weight:600; font-size:0.9rem; margin-bottom:0.15rem;">
            ECI Foam Systems CRM
        </p>
        <p style="color:{MUTED_TEXT}; font-size:0.8rem; margin:0;">
            Logged in as:<br><strong>{st.session_state["user_email"]}</strong>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")

# Logout option
if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None
    st.experimental_rerun()

# ============================================================
# HEADER (only after login)
# ============================================================

header_col1, header_col2 = st.columns([1, 3])

with header_col1:
    st.image(LOGO_URL, caption="ECI Foam Systems", use_column_width=True)

with header_col2:
    st.markdown(
        f"""
        <div class="crm-header">
            <div style="flex: 1;">
                <div class="crm-header-text-main">ECI Foam Systems CRM</div>
                <p class="crm-header-text-sub">
                    Track spray foam roofing, roof coatings, and insulation jobs – 
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
# LOAD CRM DATA
# ============================================================

df = load_data()

# For calendar: parse next_follow_up into actual dates
df_dates = df.copy()
if not df_dates.empty and "next_follow_up" in df_dates.columns:
    df_dates["next_follow_up_date"] = pd.to_datetime(
        df_dates["next_follow_up"], errors="coerce"
    ).dt.date
else:
    # empty dataframe or no column yet: create empty column
    df_dates["next_follow_up_date"] = pd.Series(dtype="object")

# ============================================================
# STATS ROW
# ============================================================

total_records = len(df)
open_statuses = ["New Lead", "Contacted", "Quoted", "Scheduled", "In Progress"]
open_records = df[df["status"].isin(open_statuses)].shape[0] if not df.empty else 0
completed_records = df[df["status"] == "Completed"].shape[0] if not df.empty else 0
lost_records = df[df["status"] == "Lost"].shape[0] if not df.empty else 0

today = date.today()
today_followups = 0
if not df_dates.empty and "next_follow_up_date" in df_dates.columns:
    today_followups = df_dates[
        df_dates["next_follow_up_date"] == today
    ].shape[0]

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
            <div class="stat-label">Today's Follow-Ups</div>
            <div class="stat-number">{today_followups}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")  # spacer

# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Filters")

status_options = ["All"] + sorted([s for s in df["status"].dropna().unique()]) if not df.empty else ["All"]
status_filter = st.sidebar.selectbox("Status", status_options)

city_options = ["All"] + sorted([c for c in df["city"].dropna().unique()]) if not df.empty else ["All"]
city_filter = st.sidebar.selectbox("City", city_options)

service_options = ["All"] + sorted([s for s in df["service_type"].dropna().unique()]) if not df.empty else ["All"]
service_filter = st.sidebar.selectbox("Service Type", service_options)

search_text = st.sidebar.text_input("Search customer / company / address", "")

sort_by = st.sidebar.selectbox(
    "Sort By",
    [
        "None",
        "Customer Name",
        "Company",
        "City",
        "Status",
        "Next Follow-Up",
        "Estimated Value",
    ],
)

# Apply filters
filtered = df.copy()

if not filtered.empty:
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

    # Sorting
    sort_map = {
        "Customer Name": "customer_name",
        "Company": "company_name",
        "City": "city",
        "Status": "status",
        "Next Follow-Up": "next_follow_up",
        "Estimated Value": "estimated_value",
    }
    if sort_by != "None" and sort_map.get(sort_by) in filtered.columns:
        filtered = filtered.sort_values(by=sort_map[sort_by], na_position="last")

# ============================================================
# TABS (VIEW / ADD / EDIT / EMAIL / CALENDAR)
# ============================================================

tab_view, tab_add, tab_edit, tab_email, tab_calendar = st.tabs(
    [
        "Customers & Leads",
        "Add Customer / Lead",
        "Edit Customer / Lead",
        "Email Client",
        "Calendar & Reminders",
    ]
)

# ------------------------------------------------------------
# TAB 1: VIEW
# ------------------------------------------------------------

with tab_view:
    st.subheader(f"Customers & Leads ({len(filtered) if not filtered.empty else 0})")

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
    existing_cols = [c for c in display_cols if c in filtered.columns] if not filtered.empty else []

    st.markdown('<div class="crm-card">', unsafe_allow_html=True)
    if not filtered.empty and existing_cols:
        st.dataframe(filtered[existing_cols], use_container_width=True)
    else:
        st.write("No records match your filters yet.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.download_button(
        label="Download filtered as CSV",
        data=(filtered.to_csv(index=False) if not filtered.empty else ""),
        file_name="sprayfoam_crm_filtered.csv",
        mime="text/csv",
    )

    # Quick update panel (status + follow-up) without going to Edit tab
    if not df.empty:
        with st.expander("Quick Update: Status & Follow-Up", expanded=False):
            df_quick = df.copy()
            df_quick["label_quick"] = (
                df_quick["customer_name"].fillna("")
                + " | "
                + df_quick["company_name"].fillna("")
                + " | "
                + df_quick["address"].fillna("")
            )
            selected_label_q = st.selectbox(
                "Choose a record",
                df_quick["label_quick"].tolist(),
                key="quick_select",
            )
            row_q = df_quick[df_quick["label_quick"] == selected_label_q].iloc[0]
            idx_q = df_quick[df_quick["label_quick"] == selected_label_q].index[0]

            current_status = row_q.get("status", "New Lead")
            status_idx = STATUS_CHOICES.index(current_status) if current_status in STATUS_CHOICES else 0
            status_q = st.selectbox("Status", STATUS_CHOICES, index=status_idx)

            nf_val = row_q.get("next_follow_up", str(today))
            nf_parsed = pd.to_datetime(nf_val, errors="coerce")
            if pd.isna(nf_parsed):
                nf_parsed = pd.Timestamp(today)
            nf_q = st.date_input("Next Follow-Up Date", value=nf_parsed.date(), key="quick_date")

            if st.button("Save Quick Update"):
                df.at[idx_q, "status"] = status_q
                df.at[idx_q, "next_follow_up"] = str(nf_q)
                save_data(df)
                st.success("Quick update saved.")
                st.experimental_rerun()

# ------------------------------------------------------------
# TAB 2: ADD CUSTOMER / LEAD
# ------------------------------------------------------------

with tab_add:
    st.subheader("Add Customer / Lead")

    with st.form("add_lead_form"):
        # CUSTOMER INFO
        st.markdown("#### Customer Information")
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
        st.markdown("#### Job / Spray Foam Details")
        c3, c4 = st.columns(2)

        with c3:
            lead_source = st.selectbox(
                "Lead Source",
                ["", "Referral", "Google", "Website", "Facebook", "Cold Call", "Repeat Customer", "Other"],
            )
            building_type = st.selectbox(
                "Building Type",
                [""] + BUILDING_TYPES,
            )
            service_type = st.selectbox(
                "Service Type",
                [""] + SERVICE_TYPES,
            )

        with c4:
            roof_type = st.selectbox(
                "Roof Type",
                [""] + ROOF_TYPES,
            )
            square_feet = st.text_input("Approx. Square Feet (roof/area)")
            estimated_value = st.text_input("Estimated Job Value ($)")
            status = st.selectbox(
                "Status",
                STATUS_CHOICES,
            )
            next_follow_up = st.date_input(
                "Next Follow-Up Date",
                value=today,
            )

        notes = st.text_area("Notes (scope, conditions, objections, etc.)")

        submitted = st.form_submit_button("Save")

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
            st.markdown("#### Customer Information")
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

            st.markdown("#### Job / Spray Foam Details")
            c3, c4 = st.columns(2)

            with c3:
                lead_source_e = st.text_input(
                    "Lead Source", value=selected_row.get("lead_source", "")
                )
                building_choices = [""] + BUILDING_TYPES
                building_current = selected_row.get("building_type", "")
                building_idx = (
                    building_choices.index(building_current)
                    if building_current in building_choices
                    else 0
                )
                building_type_e = st.selectbox(
                    "Building Type",
                    building_choices,
                    index=building_idx,
                )
                service_choices = [""] + SERVICE_TYPES
                service_current = selected_row.get("service_type", "")
                service_idx = (
                    service_choices.index(service_current)
                    if service_current in service_choices
                    else 0
                )
                service_type_e = st.selectbox(
                    "Service Type",
                    service_choices,
                    index=service_idx,
                )

            with c4:
                roof_choices = [""] + ROOF_TYPES
                roof_current = selected_row.get("roof_type", "")
                roof_idx = (
                    roof_choices.index(roof_current)
                    if roof_current in roof_choices
                    else 0
                )
                roof_type_e = st.selectbox(
                    "Roof Type",
                    roof_choices,
                    index=roof_idx,
                )
                square_feet_e = st.text_input(
                    "Approx. Square Feet", value=str(selected_row.get("square_feet", ""))
                )
                estimated_value_e = st.text_input(
                    "Estimated Job Value ($)",
                    value=str(selected_row.get("estimated_value", "")),
                )
                status_current = selected_row.get("status", "New Lead")
                status_idx = (
                    STATUS_CHOICES.index(status_current)
                    if status_current in STATUS_CHOICES
                    else 0
                )
                status_e = st.selectbox(
                    "Status",
                    STATUS_CHOICES,
                    index=status_idx,
                )
                next_follow_up_e = st.date_input(
                    "Next Follow-Up Date",
                    value=pd.to_datetime(
                        selected_row.get("next_follow_up", today)
                    ).date(),
                )

            notes_e = st.text_area(
                "Notes", value=selected_row.get("notes", "")
            )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                update_btn = st.form_submit_button("Update")
            with col_btn2:
                delete_btn = st.form_submit_button("Delete")

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

# ------------------------------------------------------------
# TAB 4: EMAIL CLIENT (YAHOO)
# ------------------------------------------------------------

with tab_email:
    st.subheader("Email Client (Yahoo)")
    st.markdown(
        "Use your **Yahoo email + app password** to email customers directly from the CRM."
    )
    st.markdown(
        "*Tip: In Yahoo account security, create an **app password** for SMTP "
        "and use it here (not your main password).*"
    )

    col_left, col_right = st.columns(2)

    with col_left:
        yahoo_email = st.text_input("Your Yahoo Email (From)")
        yahoo_app_password = st.text_input(
            "Yahoo App Password",
            type="password",
            help="Use a Yahoo app password, not your main login password.",
        )

        if df.empty:
            st.info("No customers in CRM yet to email.")
            selected_email = ""
            selected_name = ""
        else:
            df["label_email"] = (
                df["customer_name"].fillna("")
                + " | "
                + df["company_name"].fillna("")
                + " | "
                + df["email"].fillna("")
            )
            selected_label_email = st.selectbox(
                "Select customer to email", df["label_email"].tolist()
            )
            row_email = df[df["label_email"] == selected_label_email].iloc[0]
            selected_email = row_email.get("email", "")
            selected_name = row_email.get("customer_name", "")

    with col_right:
        to_email = st.text_input("To", value=selected_email)
        default_subject = "Regarding your spray foam roofing / coating project"
        subject = st.text_input("Subject", value=default_subject)

        default_body = ""
        if selected_name:
            default_body = f"Hi {selected_name},\n\n"
        default_body += (
            "Just following up about your spray foam / roof coating project.\n\n"
            "Let me know a good time to connect or if you have any questions.\n\n"
            "Best regards,\n"
            "ECI Foam Systems"
        )

        body = st.text_area("Message", value=default_body, height=220)

    if st.button("Send Email"):
        if not (yahoo_email and yahoo_app_password and to_email and subject and body):
            st.error("All fields (From, app password, To, subject, message) are required.")
        else:
            try:
                send_yahoo_email(
                    from_email=yahoo_email,
                    app_password=yahoo_app_password,
                    to_email=to_email,
                    subject=subject,
                    body=body,
                )
                st.success("Email sent successfully.")
            except Exception as e:
                st.error(f"Failed to send email: {e}")

# ------------------------------------------------------------
# TAB 5: CALENDAR & REMINDERS – MONTH VIEW WITH NOTES
# ------------------------------------------------------------

with tab_calendar:
    st.subheader("Calendar & Reminders – Month View")

    # Load calendar notes and parse dates
    notes_df = load_calendar_notes()
    if not notes_df.empty:
        notes_df["date"] = pd.to_datetime(notes_df["date"], errors="coerce").dt.date

    # Let user pick any date; we use its month & year for the grid
    selected_date = st.date_input("Choose a month to view", value=today)
    year = selected_date.year
    month = selected_date.month

    # Boundaries of that month
    month_start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    month_end = date(year, month, last_day)

    # Filter follow-ups within that month (may be empty)
    if not df_dates.empty and "next_follow_up_date" in df_dates.columns:
        month_rows = df_dates[
            (df_dates["next_follow_up_date"] >= month_start)
            & (df_dates["next_follow_up_date"] <= month_end)
        ].copy()
    else:
        month_rows = pd.DataFrame(columns=df_dates.columns)

    # Filter notes within that month
    if not notes_df.empty:
        notes_month = notes_df[
            (notes_df["date"] >= month_start) & (notes_df["date"] <= month_end)
        ].copy()
    else:
        notes_month = pd.DataFrame(columns=["date", "note"])

    month_name = calendar.month_name[month]
    st.markdown(
        f"Showing follow-ups for **{month_name} {year}** "
        f"({month_start.strftime('%b %d')} – {month_end.strftime('%b %d')})."
    )

    # Build a month grid similar to Google Calendar
    cal = calendar.Calendar(firstweekday=6)  # 6 = Sunday start (Sun–Sat)

    cal_html_parts = []
    cal_html_parts.append(
        f"""
        <div class="crm-card" style="margin-bottom: 1rem;">
            <h4 style="margin-top:0; margin-bottom:0.5rem;">{month_name} {year}</h4>
            <table style="width:100%; border-collapse:collapse; text-align:center; font-size:0.8rem;">
                <thead>
                    <tr>
        """
    )

    # Weekday headers
    for wd in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
        cal_html_parts.append(
            f'<th style="padding:0.4rem; border-bottom:1px solid {BORDER_COLOR}; '
            f'color:{MUTED_TEXT}; font-weight:600;">{wd}</th>'
        )

    cal_html_parts.append("</tr></thead><tbody>")

    # Weeks & days
    for week in cal.monthdayscalendar(year, month):
        cal_html_parts.append("<tr>")
        for day_num in week:
            if day_num == 0:
                # Empty cell (days from previous/next month)
                cal_html_parts.append(
                    '<td style="padding:6px; height:110px; border:1px solid '
                    f'{BORDER_COLOR}; background-color:#f9fafb;"></td>'
                )
            else:
                day_date = date(year, month, day_num)

                # All follow-ups for this exact date
                if not month_rows.empty and "next_follow_up_date" in month_rows.columns:
                    day_rows = month_rows[
                        month_rows["next_follow_up_date"] == day_date
                    ]
                else:
                    day_rows = pd.DataFrame(columns=month_rows.columns)

                # Any custom calendar note for this date
                note_text = ""
                if not notes_month.empty:
                    match_note = notes_month[notes_month["date"] == day_date]
                    if not match_note.empty:
                        note_text = str(match_note.iloc[0]["note"]).strip()

                has_events = not day_rows.empty
                has_note = bool(note_text)
                is_today = (day_date == today)

                # Base style for the day cell
                cell_style = (
                    "padding:6px; height:110px; vertical-align:top; "
                    f"border:1px solid {BORDER_COLOR}; text-align:left; "
                    "background-color:#ffffff;"
                )

                if has_events or has_note:
                    cell_style = cell_style.replace(
                        "background-color:#ffffff;",
                        "background-color:rgba(37,99,235,0.04);"
                    )
                if is_today:
                    cell_style += f" box-shadow:0 0 0 2px {ACCENT_COLOR} inset;"

                # Build inner HTML: day number + events + optional note
                cell_inner_parts = []
                cell_inner_parts.append(
                    f'<div style="font-weight:600; font-size:0.8rem; '
                    f'margin-bottom:4px; color:{TEXT_COLOR};">{day_num}</div>'
                )

                # Show up to 3 follow-ups
                if has_events:
                    for _, r in day_rows.head(3).iterrows():
                        name = (r.get("customer_name") or r.get("company_name") or "Job")
                        name = name.strip()
                        if len(name) > 22:
                            name = name[:21] + "…"

                        service = (r.get("service_type") or "").strip()
                        service_txt = f" – {service}" if service else ""

                        cell_inner_parts.append(
                            '<div style="font-size:0.72rem; padding:2px 4px; '
                            'margin-bottom:2px; border-radius:4px; '
                            f'background-color:rgba(37,99,235,0.12); color:{TEXT_COLOR}; '
                            'overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">'
                            f'{name}{service_txt}'
                            '</div>'
                        )

                    # If more than 3, show "+X more"
                    extra = len(day_rows) - 3
                    if extra > 0:
                        cell_inner_parts.append(
                            '<div style="font-size:0.7rem; color:#4b5563;">'
                            f'+{extra} more…'
                            '</div>'
                        )

                # Custom note for that date (wrapping text)
                if has_note:
                    cell_inner_parts.append(
                        '<div style="font-size:0.7rem; margin-top:4px; '
                        'color:#374151; white-space:normal; line-height:1.2;">'
                        f'{note_text}'
                        '</div>'
                    )

                cell_inner_html = "".join(cell_inner_parts)
                cal_html_parts.append(
                    f'<td style="{cell_style}">{cell_inner_html}</td>'
                )

        cal_html_parts.append("</tr>")

    cal_html_parts.append("</tbody></table></div>")
    cal_html = "".join(cal_html_parts)

    st.markdown(cal_html, unsafe_allow_html=True)

    # ---------- NOTE EDITOR ----------
    st.markdown("### Add or Edit Calendar Note")

    with st.form("calendar_note_form"):
        note_date = st.date_input("Date", value=selected_date, key="note_date")

        # Load latest notes again (in case something changed)
        notes_df_current = load_calendar_notes()
        if not notes_df_current.empty:
            notes_df_current["date"] = pd.to_datetime(
                notes_df_current["date"], errors="coerce"
            ).dt.date

        existing_note = ""
        if not notes_df_current.empty:
            match = notes_df_current[notes_df_current["date"] == note_date]
            if not match.empty:
                existing_note = str(match.iloc[0]["note"])

        note_text_input = st.text_area(
            "Note for this date (this will appear inside the calendar day)",
            value=existing_note,
            height=80,
        )

        col_n1, col_n2 = st.columns(2)
        with col_n1:
            save_note_btn = st.form_submit_button("Save Note")
        with col_n2:
            delete_note_btn = st.form_submit_button("Delete Note")

    if save_note_btn:
        notes_df_save = load_calendar_notes()
        if not notes_df_save.empty:
            notes_df_save["date"] = pd.to_datetime(
                notes_df_save["date"], errors="coerce"
            ).dt.date
            mask = notes_df_save["date"] == note_date
        else:
            mask = None

        if notes_df_save.empty or mask is None or not mask.any():
            new_row = {
                "date": note_date.isoformat(),
                "note": note_text_input.strip(),
            }
            notes_df_save = pd.concat(
                [notes_df_save, pd.DataFrame([new_row])],
                ignore_index=True,
            )
        else:
            notes_df_save.loc[mask, "note"] = note_text_input.strip()

        save_calendar_notes(notes_df_save)
        st.success("Note saved for this date.")
        st.experimental_rerun()

    if delete_note_btn:
        notes_df_del = load_calendar_notes()
        if not notes_df_del.empty:
            notes_df_del["date"] = pd.to_datetime(
                notes_df_del["date"], errors="coerce"
            ).dt.date
            notes_df_del = notes_df_del[notes_df_del["date"] != note_date]
            save_calendar_notes(notes_df_del)
            st.success("Note deleted for this date.")
            st.experimental_rerun()

    # ---------- Optional: table of follow-ups for the month ----------
    if not month_rows.empty:
        show_cols = [
            "next_follow_up_date",
            "customer_name",
            "company_name",
            "city",
            "service_type",
            "status",
            "phone",
            "email",
        ]
        available_cols = [c for c in show_cols if c in month_rows.columns]
        month_display = month_rows[available_cols].rename(
            columns={"next_follow_up_date": "follow_up_date"}
        ).sort_values("follow_up_date")

        st.markdown("### Follow-Ups in This Month")
        st.markdown('<div class="crm-card">', unsafe_allow_html=True)
        st.dataframe(month_display, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
