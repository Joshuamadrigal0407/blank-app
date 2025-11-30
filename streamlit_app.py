import streamlit as st
import pandas as pd
import os
import uuid
from datetime import date

DATA_FILE = "sprayfoam_crm.csv"

# -----------------------------
# Helpers to load/save data
# -----------------------------
def load_data():
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
    if "id" not in df.columns:
        df["id"] = [str(uuid.uuid4()) for _ in range(len(df))]
    return df


def save_data(df: pd.DataFrame):
    df.to_csv(DATA_FILE, index=False)


def new_id():
    return str(uuid.uuid4())


# -----------------------------
# Streamlit UI setup
# -----------------------------
st.set_page_config(page_title="Spray Foam CRM", layout="wide")

st.title("🧯 Spray Foam Business CRM")
st.caption(
    "Track spray foam and roof coating leads, quotes, jobs, and follow-ups. "
    "All data is stored locally in 'sprayfoam_crm.csv' in this folder."
)

df = load_data()

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("🔍 Filters")

status_options = ["All"] + sorted([s for s in df["status"].dropna().unique()])
status_filter = st.sidebar.selectbox("Status", status_options)

city_options = ["All"] + sorted([c for c in df["city"].dropna().unique()])
city_filter = st.sidebar.selectbox("City", city_options)

service_options = ["All"] + sorted([s for s in df["service_type"].dropna().unique()])
service_filter = st.sidebar.selectbox("Service Type", service_options)

search_text = st.sidebar.text_input("Search name / company / address", "")

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

# -----------------------------
# Tabs
# -----------------------------
tab_view, tab_add, tab_edit = st.tabs(["📋 Leads", "➕ Add Lead", "✏️ Edit Lead"])

# -----------------------------
# View tab
# -----------------------------
with tab_view:
    st.subheader(f"Leads ({len(filtered)})")

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

    st.dataframe(filtered[existing_cols], use_container_width=True)

    st.download_button(
        label="📥 Download filtered as CSV",
        data=filtered.to_csv(index=False),
        file_name="sprayfoam_crm_filtered.csv",
        mime="text/csv",
    )

# -----------------------------
# Add Lead tab
# -----------------------------
with tab_add:
    st.subheader("Add New Lead")

    with st.form("add_lead_form"):
        c1, c2 = st.columns(2)

        with c1:
            customer_name = st.text_input("Customer Name *")
            company_name = st.text_input("Company Name (optional)")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            address = st.text_input("Job / Property Address")
            city = st.text_input("City")
            state_val = st.text_input("State", value="CA")
            zip_code = st.text_input("ZIP Code")

        with c2:
            lead_source = st.selectbox(
                "Lead Source",
                ["", "Referral", "Google", "Website", "Facebook", "Cold Call", "Other"],
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
            roof_type = st.selectbox(
                "Roof Type",
                ["", "Flat", "Metal", "TPO/PVC", "Shingle", "Tile", "Other"],
            )
            square_feet = st.text_input("Approx. Square Feet (roof/area)")
            estimated_value = st.text_input("Estimated Job Value ($)")
            status = st.selectbox(
                "Status",
                [
                    "New",
                    "Contacted",
                    "Quoted",
                    "Scheduled",
                    "In Progress",
                    "Completed",
                    "Lost",
                ],
            )
            next_follow_up = st.date_input(
                "Next Follow-Up Date",
                value=date.today(),
            )

        notes = st.text_area("Notes (scope, conditions, objections, etc.)")

        submitted = st.form_submit_button("Save Lead")

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
            st.success("Lead saved.")
            st.experimental_rerun()

# -----------------------------
# Edit Lead tab
# -----------------------------
with tab_edit:
    st.subheader("Edit Existing Lead")

    if df.empty:
        st.info("No leads to edit yet. Add some leads first.")
    else:
        df["label"] = (
            df["customer_name"].fillna("")
            + " | "
            + df["company_name"].fillna("")
            + " | "
            + df["address"].fillna("")
        )

        selected_label = st.selectbox("Select a lead", df["label"].tolist())
        selected_row = df[df["label"] == selected_label].iloc[0]
        selected_idx = df[df["label"] == selected_label].index[0]

        with st.form("edit_lead_form"):
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

            with c2:
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
                        "New",
                        "Contacted",
                        "Quoted",
                        "Scheduled",
                        "In Progress",
                        "Completed",
                        "Lost",
                    ],
                    index=[
                        "New",
                        "Contacted",
                        "Quoted",
                        "Scheduled",
                        "In Progress",
                        "Completed",
                        "Lost",
                    ].index(selected_row.get("status", "New"))
                    if selected_row.get("status", "New") in
                       [
                           "New",
                           "Contacted",
                           "Quoted",
                           "Scheduled",
                           "In Progress",
                           "Completed",
                           "Lost",
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
                update_btn = st.form_submit_button("💾 Update Lead")
            with col_btn2:
                delete_btn = st.form_submit_button("🗑️ Delete Lead")

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
            st.success("Lead updated.")
            st.experimental_rerun()

        if delete_btn:
            df = df.drop(index=selected_idx)
            df = df.drop(columns=["label"], errors="ignore")
            df.reset_index(drop=True, inplace=True)
            save_data(df)
            st.success("Lead deleted.")
            st.experimental_rerun()

