import streamlit as st
import pandas as pd
import os
import uuid
from datetime import date

DATA_FILE = "crm_data.csv"

# -----------------------------
# Helpers to load/save data
# -----------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        cols = [
            "id",
            "owner_name",
            "business_name",
            "property_address",
            "city",
            "state",
            "zip_code",
            "email",
            "phone",
            "status",
            "source",
            "next_follow_up",
            "notes",
        ]
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(DATA_FILE)
    # make sure id column exists
    if "id" not in df.columns:
        df["id"] = [str(uuid.uuid4()) for _ in range(len(df))]
    return df


def save_data(df: pd.DataFrame):
    df.to_csv(DATA_FILE, index=False)


def generate_id():
    return str(uuid.uuid4())


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Simple CRM", layout="wide")

st.title("📇 Simple CRM for Property & Owner Leads")

st.caption(
    "Add, view, filter, and update your commercial/industrial property leads. "
    "Data is stored locally in `crm_data.csv` in this folder."
)

df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Filters")

status_options = ["All"] + sorted([s for s in df["status"].dropna().unique()])
status_filter = st.sidebar.selectbox("Status", status_options)

city_options = ["All"] + sorted([c for c in df["city"].dropna().unique()])
city_filter = st.sidebar.selectbox("City", city_options)

search_text = st.sidebar.text_input("Search owner / business / address", "")

# Apply filters
filtered_df = df.copy()

if status_filter != "All":
    filtered_df = filtered_df[filtered_df["status"] == status_filter]

if city_filter != "All":
    filtered_df = filtered_df[filtered_df["city"] == city_filter]

if search_text.strip():
    q = search_text.strip().lower()
    mask = (
        filtered_df["owner_name"].fillna("").str.lower().str.contains(q)
        | filtered_df["business_name"].fillna("").str.lower().str.contains(q)
        | filtered_df["property_address"].fillna("").str.lower().str.contains(q)
    )
    filtered_df = filtered_df[mask]

# Tabs: View / Add / Edit
tab_view, tab_add, tab_edit = st.tabs(["📋 View Leads", "➕ Add Lead", "✏️ Edit Lead"])

# -----------------------------
# View tab
# -----------------------------
with tab_view:
    st.subheader(f"Leads ({len(filtered_df)})")

    display_cols = [
        "owner_name",
        "business_name",
        "property_address",
        "city",
        "state",
        "zip_code",
        "email",
        "phone",
        "status",
        "next_follow_up",
        "source",
    ]

    existing_cols = [c for c in display_cols if c in filtered_df.columns]

    st.dataframe(filtered_df[existing_cols], use_container_width=True)

    st.download_button(
        label="📥 Download filtered as CSV",
        data=filtered_df.to_csv(index=False),
        file_name="crm_filtered_export.csv",
        mime="text/csv",
    )

# -----------------------------
# Add tab
# -----------------------------
with tab_add:
    st.subheader("Add New Lead")

    with st.form("add_lead_form"):
        col1, col2 = st.columns(2)

        with col1:
            owner_name = st.text_input("Owner Name")
            business_name = st.text_input("Business Name (optional)")
            property_address = st.text_input("Property Address")
            city = st.text_input("City")
            state_val = st.text_input("State", value="CA")
            zip_code = st.text_input("ZIP Code")

        with col2:
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            status = st.selectbox(
                "Status",
                ["New", "Contacted", "Quoted", "Follow-up", "Closed Won", "Closed Lost"],
            )
            source = st.text_input("Source (e.g. PRadar, Open Data, Referral)")
            next_follow_up = st.date_input(
                "Next follow-up date",
                value=date.today(),
            )

        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Save Lead")

    if submitted:
        if not owner_name and not business_name:
            st.error("Please enter at least an owner name or business name.")
        else:
            new_row = {
                "id": generate_id(),
                "owner_name": owner_name,
                "business_name": business_name,
                "property_address": property_address,
                "city": city,
                "state": state_val,
                "zip_code": zip_code,
                "email": email,
                "phone": phone,
                "status": status,
                "source": source,
                "next_follow_up": str(next_follow_up),
                "notes": notes,
            }
            df = df.append(new_row, ignore_index=True)
            save_data(df)
            st.success("Lead saved.")
            st.experimental_rerun()

# -----------------------------
# Edit tab
# -----------------------------
with tab_edit:
    st.subheader("Edit Existing Lead")

    if df.empty:
        st.info("No leads to edit yet. Add some first.")
    else:
        # Show a selector by owner/business + address
        df["display_label"] = (
            df["owner_name"].fillna("")
            + " | "
            + df["business_name"].fillna("")
            + " | "
            + df["property_address"].fillna("")
        )

        selected_label = st.selectbox(
            "Select a lead to edit",
            df["display_label"].tolist(),
        )

        selected_row = df[df["display_label"] == selected_label].iloc[0]
        selected_index = df[df["display_label"] == selected_label].index[0]

        with st.form("edit_lead_form"):
            col1, col2 = st.columns(2)

            with col1:
                owner_name_e = st.text_input(
                    "Owner Name", value=selected_row.get("owner_name", "")
                )
                business_name_e = st.text_input(
                    "Business Name", value=selected_row.get("business_name", "")
                )
                property_address_e = st.text_input(
                    "Property Address", value=selected_row.get("property_address", "")
                )
                city_e = st.text_input("City", value=selected_row.get("city", ""))
                state_e = st.text_input("State", value=selected_row.get("state", "CA"))
                zip_code_e = st.text_input(
                    "ZIP Code", value=selected_row.get("zip_code", "")
                )

            with col2:
                email_e = st.text_input("Email", value=selected_row.get("email", ""))
                phone_e = st.text_input("Phone", value=selected_row.get("phone", ""))
                status_e = st.selectbox(
                    "Status",
                    [
                        "New",
                        "Contacted",
                        "Quoted",
                        "Follow-up",
                        "Closed Won",
                        "Closed Lost",
                    ],
                    index=[
                        "New",
                        "Contacted",
                        "Quoted",
                        "Follow-up",
                        "Closed Won",
                        "Closed Lost",
                    ].index(selected_row.get("status", "New"))
                    if selected_row.get("status", "New") in [
                        "New",
                        "Contacted",
                        "Quoted",
                        "Follow-up",
                        "Closed Won",
                        "Closed Lost",
                    ]
                    else 0,
                )
                source_e = st.text_input(
                    "Source", value=selected_row.get("source", "")
                )
                next_follow_up_e = st.date_input(
                    "Next follow-up date",
                    value=pd.to_datetime(
                        selected_row.get("next_follow_up", date.today())
                    ).date(),
                )

            notes_e = st.text_area("Notes", value=selected_row.get("notes", ""))

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                update_btn = st.form_submit_button("💾 Update Lead")
            with col_btn2:
                delete_btn = st.form_submit_button("🗑️ Delete Lead")

        if update_btn:
            df.at[selected_index, "owner_name"] = owner_name_e
            df.at[selected_index, "business_name"] = business_name_e
            df.at[selected_index, "property_address"] = property_address_e
            df.at[selected_index, "city"] = city_e
            df.at[selected_index, "state"] = state_e
            df.at[selected_index, "zip_code"] = zip_code_e
            df.at[selected_index, "email"] = email_e
            df.at[selected_index, "phone"] = phone_e
            df.at[selected_index, "status"] = status_e
            df.at[selected_index, "source"] = source_e
            df.at[selected_index, "next_follow_up"] = str(next_follow_up_e)
            df.at[selected_index, "notes"] = notes_e

            # Drop helper column
            df = df.drop(columns=["display_label"], errors="ignore")
            save_data(df)
            st.success("Lead updated.")
            st.experimental_rerun()

        if delete_btn:
            df = df.drop(index=selected_index)
            df = df.drop(columns=["display_label"], errors="ignore")
            df.reset_index(drop=True, inplace=True)
            save_data(df)
            st.success("Lead deleted.")
            st.experimental_rerun()
