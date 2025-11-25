import streamlit as st
from datetime import date

st.set_page_config(page_title="Roofing Proposal & Slideshow", layout="wide")

# ---------- Helpers ----------
def format_currency(value: float) -> str:
    return f"${value:,.2f}"

def build_slides_from_proposal(form_data, totals):
    """Return a list of slide dicts: {'title': str, 'body': str}."""
    scope_lines = "\n".join([f"- {item}" for item in form_data["scope_items"]]) or "Scope to be determined."
    system_description = {
        "Spray Foam Roof System": "High R-value spray polyurethane foam roof system with protective white coating.",
        "TPO Restoration - Silicone": "Restoration of the existing TPO membrane using a high-solids silicone roof coating.",
        "TPO Restoration - Acrylic + Fabric": "Acrylic elastomeric roof coating system reinforced with polyester roof fabric."
    }.get(form_data["system_type"], form_data["system_type"])

    slides = []

    # Slide 1 – Title
    slides.append({
        "title": f"Roofing Proposal for {form_data['client_name'] or 'Client'}",
        "body": (
            f"Prepared for: {form_data['client_name'] or 'Client'}\n"
            f"Property: {form_data['project_address'] or 'Job Address'}\n"
            f"Date: {date.today().strftime('%B %d, %Y')}\n\n"
            f"Proposed System: {form_data['system_type']}"
        )
    })

    # Slide 2 – Scope
    slides.append({
        "title": "Scope of Work",
        "body": (
            f"Roof Area: {form_data['roof_area']} sq ft\n"
            f"Existing Roof: {form_data['existing_roof'] or 'Existing system'}\n\n"
            f"Planned work:\n{scope_lines}"
        )
    })

    # Slide 3 – System Overview
    slides.append({
        "title": "System Overview",
        "body": (
            f"{system_description}\n\n"
            f"Warranty: {form_data['warranty_term']}\n"
            f"Color/Finish: {form_data['finish_color']}"
        )
    })

    # Slide 4 – Investment Summary
    slides.append({
        "title": "Investment Summary",
        "body": (
            f"Base price: {format_currency(totals['base_price'])}\n"
            f"Tax ({form_data['tax_rate']}%): {format_currency(totals['tax_amount'])}\n"
            f"Total Investment: {format_currency(totals['total_price'])}\n\n"
            f"Price per sq ft: {format_currency(totals['price_per_sqft'])}"
        )
    })

    # Slide 5 – Notes & Next Steps
    slides.append({
        "title": "Notes & Next Steps",
        "body": (
            f"Notes:\n{form_data['notes'] or 'No special notes provided.'}\n\n"
            "Next steps:\n"
            "- Review proposal details\n"
            "- Schedule site walk / questions\n"
            "- Approve and schedule installation"
        )
    })

    return slides


def ensure_session_state():
    if "proposal_form" not in st.session_state:
        st.session_state["proposal_form"] = {}
    if "slides" not in st.session_state:
        st.session_state["slides"] = []


ensure_session_state()

# ---------- Layout ----------
st.title("Roofing Proposal & Slideshow (from Excel System)")

mode = st.sidebar.radio(
    "Choose section",
    ["Proposal Form", "Slideshow Viewer"],
)

if mode == "Proposal Form":
    st.subheader("Enter Project Details")

    with st.form("proposal_form"):
        col1, col2 = st.columns(2)

        with col1:
            client_name = st.text_input("Client name")
            project_address = st.text_input("Project address")
            existing_roof = st.text_input("Existing roof type (optional)", placeholder="Old TPO, metal, etc.")
            roof_area = st.number_input("Roof area (sq ft)", min_value=0.0, step=100.0)
            system_type = st.selectbox(
                "Proposed system",
                [
                    "Spray Foam Roof System",
                    "TPO Restoration - Silicone",
                    "TPO Restoration - Acrylic + Fabric",
                    "Other",
                ],
            )

        with col2:
            unit_price = st.number_input("Base price per sq ft ($)", min_value=0.0, step=0.10)
            tax_rate = st.number_input("Tax rate (%)", min_value=0.0, max_value=15.0, step=0.25, value=8.25)
            warranty_term = st.text_input("Warranty term", value="10-year labor & material")
            finish_color = st.text_input("Finish color", value="White reflective coating")

        st.markdown("**Scope items (check all that apply):**")
        scope_columns = st.columns(2)
        default_scope_options = [
            "Power wash roof surface",
            "Prep and prime existing roof",
            "Install spray foam / coating system",
            "Seal all roof penetrations (jacks, vents, pipes)",
            "Flash skylights and curbs",
            "Clean up and haul away debris",
        ]
        scope_selected = []
        for idx, label in enumerate(default_scope_options):
            with scope_columns[idx % 2]:
                if st.checkbox(label, key=f"scope_{idx}"):
                    scope_selected.append(label)

        notes = st.text_area("Additional notes / conditions", height=100)

        submitted = st.form_submit_button("Generate Proposal & Slides")

    if submitted:
        # Simple calculations – replace with your exact Excel logic if needed
        base_price = roof_area * unit_price
        tax_amount = base_price * (tax_rate / 100.0)
        total_price = base_price + tax_amount
        price_per_sqft = total_price / roof_area if roof_area > 0 else 0.0

        form_data = {
            "client_name": client_name,
            "project_address": project_address,
            "existing_roof": existing_roof,
            "roof_area": roof_area,
            "system_type": system_type,
            "unit_price": unit_price,
            "tax_rate": tax_rate,
            "warranty_term": warranty_term,
            "finish_color": finish_color,
            "scope_items": scope_selected,
            "notes": notes,
        }
        totals = {
            "base_price": base_price,
            "tax_amount": tax_amount,
            "total_price": total_price,
            "price_per_sqft": price_per_sqft,
        }

        st.session_state["proposal_form"] = form_data
        st.session_state["slides"] = build_slides_from_proposal(form_data, totals)

        st.success("Proposal generated! Scroll down to preview, or click **Slideshow Viewer** in the sidebar.")

        st.markdown("### Proposal Preview (Text)")
        proposal_text = f"""
Roofing Proposal
================

Client: {client_name or 'Client'}
Property: {project_address or 'Job Address'}
Date: {date.today().strftime('%B %d, %Y')}

Proposed System
---------------
{system_type}
Existing roof: {existing_roof or 'Existing system'}

Scope of Work
-------------
"""
        for item in scope_selected:
            proposal_text += f"- {item}\n"

        proposal_text += f"""

Roof Area: {roof_area} sq ft
Warranty: {warranty_term}
Finish color: {finish_color}

Investment Summary
------------------
Base price: {format_currency(base_price)}
Tax ({tax_rate}%): {format_currency(tax_amount)}
Total investment: {format_currency(total_price)}
Price per sq ft: {format_currency(price_per_sqft)}

Notes
-----
{notes or 'No special notes.'}
"""
        st.code(proposal_text, language="markdown")

        st.download_button(
            "Download proposal as text file",
            data=proposal_text,
            file_name="roofing_proposal.txt",
            mime="text/plain",
        )

elif mode == "Slideshow Viewer":
    st.subheader("Slideshow Viewer")

    slides = st.session_state.get("slides", [])

    if not slides:
        st.info("No slides yet. Go to **Proposal Form** first and generate a proposal.")
    else:
        slide_titles = [f"{i+1}. {s['title']}" for i, s in enumerate(slides)]
        selected_index = st.slider(
            "Slide number",
            min_value=1,
            max_value=len(slides),
            value=1,
        ) - 1

        slide = slides[selected_index]

        st.markdown(f"### {slide['title']}")
        st.markdown(
            slide["body"].replace("\n", "  \n")
        )

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("Previous", disabled=selected_index == 0):
                st.session_state["_slide_index"] = max(0, selected_index - 1)
        with col_next:
            if st.button("Next", disabled=selected_index == len(slides) - 1):
                st.session_state["_slide_index"] = min(len(slides) - 1, selected_index + 1)

        st.caption("Tip: Put your browser in full-screen mode when presenting to the client.")
