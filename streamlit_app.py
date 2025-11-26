import streamlit as st
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from datetime import date

st.set_page_config(page_title="Spray Foam Roof System & Slideshow", layout="wide")


# ---------- Data structures ----------
@dataclass
class RoofSection:
    name: str
    corr_factor: float  # same as your Excel CORR % column (0.1 = 10% extra)
    length: float
    width: float
    depth: float  # inches or whatever unit you use in the sheet


@dataclass
class FoamTotals:
    total_sqft: float
    total_board_feet: float
    total_base_gal: float
    total_top_gal: float
    foam_yield_bdft_per_lb: float
    total_foam_lbs: float


# ---------- Helpers ----------
def calc_section(section: RoofSection,
                 base_rate_per_100_sqft: float,
                 top_rate_per_100_sqft: float) -> Dict[str, Any]:
    """
    Replicates your Excel formulas conceptually:

    E (SQ.FT.) = LENGTH * WIDTH
    G (FEET / board ft) = F * E + F * E * B  = F * E * (1 + B)
    H (Base Coat gal)  = E/100 * H4 + E/100 * H4 * B = (E/100 * H4) * (1 + B)
    I (Top Coat gal)   = (E/100 * I4) * (1 + B)

    where:
    - B is your CORR factor (you labeled as %, but in Excel it's used directly)
    - H4 and I4 are both 2 in your sheet.
    """
    corr = section.corr_factor or 0.0
    sqft = (section.length or 0.0) * (section.width or 0.0)

    board_feet = (section.depth or 0.0) * sqft * (1.0 + corr)
    base_gal = (sqft / 100.0) * base_rate_per_100_sqft * (1.0 + corr)
    top_gal = (sqft / 100.0) * top_rate_per_100_sqft * (1.0 + corr)

    return {
        "name": section.name,
        "corr_factor": corr,
        "length": section.length,
        "width": section.width,
        "depth": section.depth,
        "sqft": sqft,
        "board_feet": board_feet,
        "base_gal": base_gal,
        "top_gal": top_gal,
    }


def calc_totals(sections: List[RoofSection],
                base_rate_per_100_sqft: float,
                top_rate_per_100_sqft: float,
                foam_yield_bdft_per_lb: float) -> FoamTotals:
    rows = [calc_section(s, base_rate_per_100_sqft, top_rate_per_100_sqft) for s in sections]

    total_sqft = sum(r["sqft"] for r in rows)
    total_board_feet = sum(r["board_feet"] for r in rows)
    total_base_gal = sum(r["base_gal"] for r in rows)
    total_top_gal = sum(r["top_gal"] for r in rows)

    foam_lbs = total_board_feet / foam_yield_bdft_per_lb if foam_yield_bdft_per_lb > 0 else 0.0

    return FoamTotals(
        total_sqft=total_sqft,
        total_board_feet=total_board_feet,
        total_base_gal=total_base_gal,
        total_top_gal=total_top_gal,
        foam_yield_bdft_per_lb=foam_yield_bdft_per_lb,
        total_foam_lbs=foam_lbs,
    )


def fmt_money(value: float) -> str:
    return f"${value:,.2f}"


def fmt_num(value: float, decimals: int = 2) -> str:
    return f"{value:,.{decimals}f}"


def build_slides(client_data: Dict[str, Any],
                 foam_totals: FoamTotals,
                 system_description: str,
                 price_data: Dict[str, float]) -> List[Dict[str, str]]:
    """
    Build a simple text-based slide deck (each slide is a dict with title/body).
    """
    slides = []

    # Slide 1 – Title
    slides.append({
        "title": f"Roofing Proposal for {client_data['client_name'] or 'Client'}",
        "body": (
            f"Prepared for: {client_data['client_name'] or 'Client'}\n"
            f"Property: {client_data['project_address'] or 'Job Address'}\n"
            f"Date: {date.today().strftime('%B %d, %Y')}\n\n"
            f"Proposed System: {client_data['system_name']}"
        )
    })

    # Slide 2 – Scope / Area
    slides.append({
        "title": "Scope of Work & Roof Area",
        "body": (
            f"Total roof area: {fmt_num(foam_totals.total_sqft, 0)} sq ft\n"
            f"System type: {client_data['system_name']}\n\n"
            "Scope (example):\n"
            "- Power wash roof surface\n"
            "- Prep and prime existing roof\n"
            "- Install spray polyurethane foam to specified thickness\n"
            "- Apply base and top coat to manufacturer specs\n"
            "- Seal roof penetrations (jacks, vents, pipes)\n"
            "- Jobsite cleanup and haul-off"
        )
    })

    # Slide 3 – Materials / Quantities
    slides.append({
        "title": "Foam & Coating Quantities",
        "body": (
            f"Spray foam total: {fmt_num(foam_totals.total_board_feet, 0)} board feet\n"
            f"Foam yield: {fmt_num(foam_totals.foam_yield_bdft_per_lb, 2)} bd.ft./lb\n"
            f"Estimated foam weight: {fmt_num(foam_totals.total_foam_lbs, 0)} lbs\n\n"
            f"Base coat (approx.): {fmt_num(foam_totals.total_base_gal, 1)} gallons\n"
            f"Top coat (approx.):  {fmt_num(foam_totals.total_top_gal, 1)} gallons\n\n"
            f"System description:\n{system_description}"
        )
    })

    # Slide 4 – Investment
    slides.append({
        "title": "Investment Summary",
        "body": (
            f"Price per sq ft: {fmt_money(price_data['price_per_sqft'])}\n"
            f"Subtotal: {fmt_money(price_data['subtotal'])}\n"
            f"Tax ({price_data['tax_rate']}%): {fmt_money(price_data['tax_amount'])}\n"
            f"Total investment: {fmt_money(price_data['total'])}\n"
        )
    })

    # Slide 5 – Notes & Next Steps
    slides.append({
        "title": "Notes & Next Steps",
        "body": (
            f"Warranty: {client_data['warranty_term']}\n"
            f"Finish color: {client_data['finish_color']}\n\n"
            f"Notes:\n{client_data['notes'] or 'No special notes.'}\n\n"
            "Next steps:\n"
            "- Review proposal details\n"
            "- Schedule a follow-up or site walk\n"
            "- Approve proposal and schedule installation"
        )
    })

    return slides


def ensure_session_state():
    if "foam_sections" not in st.session_state:
        # Start with one sample row (similar to your sheet)
        st.session_state["foam_sections"] = [
            RoofSection(name="Main Roof", corr_factor=0.0, length=120.0, width=100.0, depth=1.5)
        ]
    if "foam_totals" not in st.session_state:
        st.session_state["foam_totals"] = None
    if "slides" not in st.session_state:
        st.session_state["slides"] = []


ensure_session_state()

# ---------- App UI ----------
st.title("Spray Foam Roof System (Excel → Software) with Slideshow")


tab_calc, tab_proposal = st.tabs(["Foam Calculator", "Proposal & Slideshow"])


# ---------- TAB 1: Foam Calculator ----------
with tab_calc:
    st.subheader("Foam Takeoff (mirrors your Excel logic)")

    col_settings, col_sections = st.columns([1, 2])

    with col_settings:
        st.markdown("**System Settings (like H4, I4 & yield in your sheet)**")
        base_rate_per_100_sqft = st.number_input(
            "Base coat gallons per 100 sq ft (H4)",
            min_value=0.0,
            value=2.0,
            step=0.1,
        )
        top_rate_per_100_sqft = st.number_input(
            "Top coat gallons per 100 sq ft (I4)",
            min_value=0.0,
            value=2.0,
            step=0.1,
        )
        foam_yield_bdft_per_lb = st.number_input(
            "Foam yield (board feet per lb) – like 3 bd.ft./lb",
            min_value=0.1,
            value=3.0,
            step=0.1,
        )

        st.markdown(
            "_Note: CORR factor works like your Excel: 0.10 = +10% foam and coating._"
        )

    with col_sections:
        st.markdown("**Roof Sections**")

        sections: List[RoofSection] = st.session_state["foam_sections"]

        new_sections: List[RoofSection] = []
        for idx, sec in enumerate(sections):
            with st.expander(f"Section {idx + 1}: {sec.name or 'Roof Area'}", expanded=(idx == 0)):
                c1, c2, c3, c4, c5 = st.columns(5)
                name = c1.text_input("Name", value=sec.name, key=f"name_{idx}")
                corr = c2.number_input("CORR factor (0.10 = 10%)", value=float(sec.corr_factor), step=0.01, key=f"corr_{idx}")
                length = c3.number_input("Length", value=float(sec.length), step=1.0, key=f"len_{idx}")
                width = c4.number_input("Width", value=float(sec.width), step=1.0, key=f"wid_{idx}")
                depth = c5.number_input("Depth", value=float(sec.depth), step=0.1, key=f"dep_{idx}")

                # Calculate live preview
                row = calc_section(
                    RoofSection(name=name, corr_factor=corr, length=length, width=width, depth=depth),
                    base_rate_per_100_sqft,
                    top_rate_per_100_sqft,
                )

                st.markdown(
                    f"- SQ.FT.: **{fmt_num(row['sqft'], 0)}**\n"
                    f"- Board feet: **{fmt_num(row['board_feet'], 0)}**\n"
                    f"- Base coat: **{fmt_num(row['base_gal'], 1)} gal**\n"
                    f"- Top coat: **{fmt_num(row['top_gal'], 1)} gal**"
                )

                new_sections.append(
                    RoofSection(name=name, corr_factor=corr, length=length, width=width, depth=depth)
                )

        st.session_state["foam_sections"] = new_sections

        col_add, col_calc = st.columns(2)
        with col_add:
            if st.button("Add another section"):
                st.session_state["foam_sections"].append(
                    RoofSection(name=f"Section {len(st.session_state['foam_sections']) + 1}",
                                corr_factor=0.0, length=0.0, width=0.0, depth=1.0)
                )
                st.experimental_rerun()

        with col_calc:
            if st.button("Calculate Totals"):
                totals = calc_totals(
                    st.session_state["foam_sections"],
                    base_rate_per_100_sqft,
                    top_rate_per_100_sqft,
                    foam_yield_bdft_per_lb,
                )
                st.session_state["foam_totals"] = totals
                st.success("Totals updated and ready for the Proposal & Slideshow tab.")

        totals: FoamTotals = st.session_state.get("foam_totals") or None
        if totals:
            st.markdown("### Totals (like your row 19 and yield)")

            st.markdown(
                f"- Total SQ.FT.: **{fmt_num(totals.total_sqft, 0)}**\n"
                f"- Total board feet: **{fmt_num(totals.total_board_feet, 0)}**\n"
                f"- Base coat total: **{fmt_num(totals.total_base_gal, 1)} gal**\n"
                f"- Top coat total: **{fmt_num(totals.total_top_gal, 1)} gal**\n"
                f"- Foam yield: **{fmt_num(totals.foam_yield_bdft_per_lb, 2)} bd.ft./lb**\n"
                f"- Estimated foam weight: **{fmt_num(totals.total_foam_lbs, 0)} lbs**"
            )


# ---------- TAB 2: Proposal & Slideshow ----------
with tab_proposal:
    st.subheader("Turn your numbers into a Proposal & Slideshow")

    totals: FoamTotals = st.session_state.get("foam_totals") or None
    if not totals:
        st.info("First, go to **Foam Calculator** and click **Calculate Totals**.")
    else:
        with st.form("proposal_form"):
            c1, c2 = st.columns(2)
            with c1:
                client_name = st.text_input("Client name")
                project_address = st.text_input("Project address")
                system_name = st.text_input(
                    "System name",
                    value="Spray Polyurethane Foam Roof System",
                )
                warranty_term = st.text_input(
                    "Warranty term",
                    value="10-year labor & material",
                )

            with c2:
                finish_color = st.text_input("Finish color", value="White reflective coating")
                price_per_sqft = st.number_input(
                    "Price per sq ft ($)",
                    min_value=0.0,
                    step=0.10,
                    value=3.50,
                )
                tax_rate = st.number_input(
                    "Tax rate (%)",
                    min_value=0.0,
                    max_value=15.0,
                    step=0.25,
                    value=8.25,
                )

            notes = st.text_area("Notes / special conditions", height=100)

            submitted = st.form_submit_button("Generate Proposal & Slides")

        if submitted:
            subtotal = totals.total_sqft * price_per_sqft
            tax_amount = subtotal * (tax_rate / 100.0)
            total_price = subtotal + tax_amount

            client_data = {
                "client_name": client_name,
                "project_address": project_address,
                "system_name": system_name,
                "warranty_term": warranty_term,
                "finish_color": finish_color,
                "notes": notes,
            }

            price_data = {
                "price_per_sqft": price_per_sqft,
                "subtotal": subtotal,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total": total_price,
            }

            system_description = (
                "Spray polyurethane foam roof system applied over the existing substrate, "
                "installed to the specified thickness and slope, with protective base and top "
                "coat to manufacturer specifications."
            )

            slides = build_slides(client_data, totals, system_description, price_data)
            st.session_state["slides"] = slides

            st.success("Proposal and slides generated. Scroll down to view them.")

            # Text proposal preview
            st.markdown("### Proposal Text Preview")
            proposal_md = f"""
Roofing Proposal
================

Client: {client_name or 'Client'}
Property: {project_address or 'Job Address'}
Date: {date.today().strftime('%B %d, %Y')}

Proposed System
---------------
{system_name}

Roof Area & Quantities
----------------------
Total roof area: {fmt_num(totals.total_sqft, 0)} sq ft  
Total foam: {fmt_num(totals.total_board_feet, 0)} board feet  
Foam yield: {fmt_num(totals.foam_yield_bdft_per_lb, 2)} bd.ft./lb  
Estimated foam weight: {fmt_num(totals.total_foam_lbs, 0)} lbs  

Base coat: {fmt_num(totals.total_base_gal, 1)} gallons  
Top coat: {fmt_num(totals.total_top_gal, 1)} gallons  

Investment
----------
Price per sq ft: {fmt_money(price_per_sqft)}  
Subtotal: {fmt_money(subtotal)}  
Tax ({tax_rate}%): {fmt_money(tax_amount)}  
Total investment: {fmt_money(total_price)}  

Warranty & Finish
-----------------
Warranty: {warranty_term}  
Finish color: {finish_color}  

Notes
-----
{notes or 'No special notes.'}
"""
            st.code(proposal_md, language="markdown")

            st.download_button(
                "Download proposal as .txt",
                data=proposal_md,
                file_name="spray_foam_roof_proposal.txt",
                mime="text/plain",
            )

        # Slideshow viewer
        slides = st.session_state.get("slides", [])
        st.markdown("### Slideshow Viewer")

        if not slides:
            st.info("Generate the proposal above to populate the slides.")
        else:
            total_slides = len(slides)
            idx = st.slider("Slide number", 1, total_slides, 1) - 1
            slide = slides[idx]

            st.markdown(f"#### {slide['title']}")
            st.markdown(slide["body"].replace("\n", "  \n"))

            col_prev, col_next = st.columns(2)
            with col_prev:
                if st.button("Previous", disabled=(idx == 0)):
                    st.session_state["slide_index"] = max(0, idx - 1)
            with col_next:
                if st.button("Next", disabled=(idx == total_slides - 1)):
                    st.session_state["slide_index"] = min(total_slides - 1, idx + 1)

            st.caption("Tip: Zoom your browser and go full screen when presenting to the client.")

