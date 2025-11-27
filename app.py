import os
import urllib.parse
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# Airtable config
# ---------------------------------------------------------------------
load_dotenv()

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
FUNDING_TABLE = os.getenv("AIRTABLE_FUNDING_TABLE", "Funding Programs")
PROJECTS_TABLE = os.getenv("AIRTABLE_PROJECTS_TABLE", "Project Submissions")

AIRTABLE_API_BASE = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}"
AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def create_project_submission(fields: dict) -> str | None:
    """Create a project submission in Airtable and return its record ID."""
    table_name_encoded = urllib.parse.quote(PROJECTS_TABLE, safe="")
    url = f"{AIRTABLE_API_BASE}/{table_name_encoded}"

    resp = requests.post(url, headers=AIRTABLE_HEADERS, json={"fields": fields})
    if resp.status_code == 200:
        return resp.json().get("id")
    else:
        st.error(f"Error saving project to Airtable: {resp.status_code} – {resp.text}")
        return None


def update_project_submission(record_id: str, fields: dict) -> None:
    """Update an existing project submission record in Airtable."""
    table_name_encoded = urllib.parse.quote(PROJECTS_TABLE, safe="")
    url = f"{AIRTABLE_API_BASE}/{table_name_encoded}/{record_id}"

    resp = requests.patch(url, headers=AIRTABLE_HEADERS, json={"fields": fields})
    if resp.status_code != 200:
        st.error(f"Error updating project: {resp.status_code} – {resp.text}")


def load_funding_programs() -> pd.DataFrame:
    """Load all funding programs from Airtable into a DataFrame."""
    table_name_encoded = urllib.parse.quote(FUNDING_TABLE, safe="")
    url = f"{AIRTABLE_API_BASE}/{table_name_encoded}"

    records = []
    offset = None

    while True:
        params = {}
        if offset:
            params["offset"] = offset

        resp = requests.get(url, headers=AIRTABLE_HEADERS, params=params)
        if resp.status_code != 200:
            st.error(f"Error reading Airtable: {resp.status_code} – {resp.text}")
            return pd.DataFrame()

        data = resp.json()
        for rec in data.get("records", []):
            fields = rec.get("fields", {})
            # store Airtable record ID so we can reference it later
            fields["id"] = rec.get("id")
            records.append(fields)

        offset = data.get("offset")
        if not offset:
            break

    return pd.DataFrame(records)


def as_list(value):
    """Normalize Airtable multi-select / text / None into a list of strings."""
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [value]
    return []


def parse_number(value):
    """Safely parse numeric or string-with-commas to float, else None."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").replace("$", ""))
        except ValueError:
            return None
    return None


def estimate_project_budget(band: str) -> float | None:
    """Rough numeric value for budget band."""
    mapping = {
        "<$50k": 25_000,
        "$50–250k": 150_000,
        "$250k–1M": 500_000,
        ">1M": 1_500_000,
    }
    return mapping.get(band)


# ---------------------------------------------------------------------
# PRD-aligned scoring (per program)
#   Region   – 30
#   Applicant – 30
#   Project type – 20
#   Themes – 10
#   Budget – 10
#   Stage bonus – +5 (clamped so total <= 100)
# ---------------------------------------------------------------------
def raw_score_program(row, applicant_type, project_types, themes, budget_range, region, stage):
    score_region = 0
    score_applicant = 0
    score_type = 0
    score_themes = 0
    score_budget = 0
    stage_bonus = 0

    # ---- Region (0–30) ----------------------------------------------
    elig_regions = as_list(
        row.get("Eligible_Regions")
        or row.get("Region")
        or row.get("Regions")
    )
    region_norm = (region or "").strip().lower()

    if region_norm:
        if not elig_regions:
            # no region data on program – neutral-ish
            score_region = 15
        else:
            if any(
                region_norm in r.lower() or r.lower() in region_norm
                for r in elig_regions
            ):
                score_region = 30
            else:
                score_region = 0
    else:
        # project region unknown – small neutral value
        score_region = 10

    # ---- Applicant (0–30) -------------------------------------------
    elig_apps = as_list(row.get("Eligible_Applicants"))
    app_norm = (applicant_type or "").lower()

    if not elig_apps:
        score_applicant = 15
    elif any(app_norm in s.lower() for s in elig_apps):
        score_applicant = 30
    else:
        score_applicant = 0

    # ---- Project type (0–20) ----------------------------------------
    elig_types = as_list(row.get("Eligible_Project_Types") or row.get("Focus_Area"))
    elig_types_norm = {s.lower() for s in elig_types}
    proj_types_norm = {pt.lower() for pt in project_types} if project_types else set()

    if proj_types_norm and elig_types_norm:
        overlap = proj_types_norm & elig_types_norm
        if overlap:
            frac = len(overlap) / len(proj_types_norm)
            score_type = int(20 * min(1.0, frac))
    elif not elig_types_norm:
        score_type = 10  # program doesn't specify – mild neutral

    # ---- Themes (0–10) ----------------------------------------------
    program_themes = as_list(
        row.get("Themes")
        or row.get("Focus_Themes")
        or row.get("Focus_Area_Themes")
    )
    program_themes_norm = {s.lower() for s in program_themes}
    proj_themes_norm = {t.lower() for t in themes} if themes else set()

    if proj_themes_norm and program_themes_norm:
        overlap = proj_themes_norm & program_themes_norm
        if overlap:
            frac = len(overlap) / len(proj_themes_norm)
            score_themes = int(10 * min(1.0, frac))
    elif not program_themes_norm:
        score_themes = 5  # no theme info – neutral

    # ---- Budget (0–10) ----------------------------------------------
    proj_budget = estimate_project_budget(budget_range)
    max_amt = parse_number(row.get("Max_Grant_Amount") or row.get("Max_Amount"))

    if proj_budget is None:
        score_budget = 5
    elif max_amt is None:
        score_budget = 5
    else:
        if proj_budget <= max_amt:
            score_budget = 10
        elif proj_budget <= 1.5 * max_amt:
            score_budget = 5
        else:
            score_budget = 0

    # ---- Stage bonus (+5) -------------------------------------------
    program_stages = as_list(
        row.get("Project_Stages")
        or row.get("Stage_Preference")
        or row.get("Stages")
    )
    stage_norm = (stage or "").lower()
    if stage_norm and program_stages:
        if any(stage_norm in s.lower() for s in program_stages):
            stage_bonus = 5

    total = score_region + score_applicant + score_type + score_themes + score_budget + stage_bonus
    total = min(total, 100)  # clamp to 100
    return float(total)


# ---------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------
st.set_page_config(page_title="Funding Matcher MVP", layout="wide")

with st.sidebar:
    st.header("ℹ️ About this prototype")
    st.markdown(
        """
        This is an early **EcoProject Navigator / Funding Matcher** demo.

        1. Tell us **who you are** and **what the project is**  
        2. Click **Find funding matches**  
        3. Your project is **saved to Airtable**  
        4. You'll see funding programs **ranked by match score**  
        5. Top match is flagged for an AI **Deep Dive Brief** (status = `pending`)
        """
    )

st.title("🌱 EcoProject Navigator – Funding Matcher MVP")
st.caption("Match restoration projects to potential funding programs.")

# ------------------- Inputs -------------------
st.markdown("## 1️⃣ Who are you?")

org_name = st.text_input("Organization")
name = st.text_input("Your name")
email = st.text_input("Email address")

applicant_type = st.selectbox(
    "Applicant type",
    [
        "First Nation",
        "Indigenous organization",
        "Municipality / Regional District",
        "Non-profit / Charity",
        "For-profit business",
        "University / Research institute",
        "Other",
    ],
)

partners = st.text_input("Key partners (optional)")
match_funding = st.selectbox(
    "Do you have match funding available?",
    ["Unsure", "Yes", "No"],
)

st.markdown("## 2️⃣ Project basics")
col1, col2 = st.columns(2)

with col1:
    region = st.text_input("Region / Watershed (e.g., 'Cowichan', 'Koksilah')")
    budget_range = st.selectbox(
        "Approximate budget range",
        ["<$50k", "$50–250k", "$250k–1M", ">1M"],
    )
    stage = st.selectbox(
        "Project stage",
        [
            "Idea",
            "Planning",
            "Ready to implement",
            "Shovel-ready",
        ],
    )

with col2:
    project_types = st.multiselect(
        "Project type(s)",
        [
            "Culvert replacement",
            "Road deactivation / upgrades",
            "Riparian planting",
            "Instream LWD / channel work",
            "Planning / assessment",
            "Monitoring",
            "Community engagement / education",
            "Land acquisition / conservation",
        ],
    )
    themes = st.multiselect(
        "Theme(s) / focus areas",
        [
            "Climate adaptation",
            "Salmon habitat",
            "Watershed health",
            "Flood resilience",
            "Wildfire resilience",
            "Forest roads & access",
            "Erosion & sediment",
            "Water quality",
            "Biodiversity",
            "Wetlands & beavers",
            "Drinking water protection",
            "Community engagement / stewardship",
        ],
    )

project_title = st.text_input("Project title")
description = st.text_area("Short project description", height=120)

st.markdown("---")

# ---------------------------------------------------------------------
# MAIN BUTTON + MATCHING LOGIC
# ---------------------------------------------------------------------
if st.button("🔍 Find funding matches"):

    # 1) Save project submission (set Deep Dive Status = pending explicitly)
    fields = {
        "Name": name,
        "Email": email,
        "Applicant Type": applicant_type,
        "Region": region,
        "Budget Range": budget_range,
        "Project Types": ", ".join(project_types) if project_types else "",
        "Project Title": project_title,
        "Description": description,
    }

    submission_id = create_project_submission(fields)
    if submission_id:
        st.success("✅ Your project was saved to Airtable.")
    else:
        st.warning("⚠️ Could not save to Airtable. Matches shown anyway.")

    # 2) Load funding programs from Airtable
    df = load_funding_programs()
    if df.empty:
        st.warning("No funding programs found in Airtable.")
        st.stop()

    # 3) Compute PRD-aligned scores (0–100)
    df["RawScore"] = df.apply(
        lambda row: raw_score_program(
            row,
            applicant_type=applicant_type,
            project_types=project_types,
            themes=themes,
            budget_range=budget_range,
            region=region,
            stage=stage,
        ),
        axis=1,
    )

    # No normalization: RawScore is already 0–100
    df["Score"] = df["RawScore"].round().astype(int)

    # 4) Sort ALL programs by score (desc) and name (asc) as tie-breaker
    df = df.sort_values(
        by=["Score", "Program_Name"],
        ascending=[False, True],
        kind="mergesort",  # stable sort
    )

    # 5) Take the top program and write it back to the submission
    if not df.empty and submission_id:
        top_program = df.iloc[0]
        top_program_id = top_program["id"]  # Airtable record ID for program

        update_fields = {
            "Top Program ID": top_program_id,
            # keep Deep Dive Status as 'pending' so your Make.com watcher can fire
        }
        update_project_submission(submission_id, update_fields)

    # 6) Display results
    st.markdown("## 3️⃣ Suggested funding programs")
    st.caption(
        "These programs are loaded directly from your Airtable base and ranked against your project using the PRD weighting."
    )

    for _, row in df.iterrows():
        with st.container():
            program_name = (
                row.get("Program_Name") or row.get("Program") or "Unnamed program"
            )
            st.markdown(f"### 🌊 {program_name}")

            # ----- Top row metrics -----
            cols = st.columns(4)
            cols[0].metric("Match score", int(row["Score"]))

            # Min / max grants
            min_grant = (
                row.get("Min_Grant_Amount")
                or row.get("Minimum_Grant")
                or row.get("Min_Amount")
                or "—"
            )
            max_grant = (
                row.get("Max_Grant_Amount")
                or row.get("Max_Amount")
                or row.get("Maximum_Grant")
                or "—"
            )
            cols[1].write(f"**Minimum grant amount:** {min_grant}")
            cols[2].write(f"**Maximum grant amount:** {max_grant}")

            # Application deadline & competitiveness
            deadline = (
                row.get("Application_Deadline")
                or row.get("Next_Deadline")
                or row.get("Deadline")
                or "—"
            )
            competitiveness = (
                row.get("Competitiveness_Level")
                or row.get("Competitive_Level")
                or row.get("Competition_Level")
                or "—"
            )
            cols[3].write(f"**Application deadline:** {deadline}")

            # Second line under metrics for competitiveness (single column)
            st.write(f"**Competitiveness level:** {competitiveness}")

            # ----- Program description -----
            description_field = (
                row.get("Program_Description") or row.get("Description")
            )
            if description_field:
                st.markdown("**Program description**")
                st.write(description_field)

            # ----- Reporting requirements -----
            reporting = (
                row.get("Reporting_Requirements")
                or row.get("Reporting")
                or row.get("Reporting_Notes")
            )
            if reporting:
                st.markdown("**Reporting requirements**")
                st.write(reporting)

            # ----- Portal link & contact email -----
            portal = (
                row.get("Application_Portal")
                or row.get("Portal_URL")
                or row.get("Website")
                or ""
            )
            contact_email = (
                row.get("Contact_Email")
                or row.get("Funder_Contact_Email")
                or row.get("Email")
                or ""
            )

            link_bits = []
            if portal:
                link_bits.append(f"[Application portal]({portal})")
            if contact_email:
                link_bits.append(f"Contact: `{contact_email}`")

            if link_bits:
                st.markdown("**How to apply**")
                st.write(" • ".join(link_bits))

            st.write("---")
