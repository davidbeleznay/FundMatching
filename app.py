import os
import urllib.parse
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from funding_templates.program_mapper import has_template
from grant_readiness_page import show_grant_readiness_page

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

    # Clean fields to handle Airtable field type issues
    clean_fields = {}
    for key, value in fields.items():
        # Convert lists to comma-separated strings for text fields
        if isinstance(value, list):
            clean_fields[key] = ", ".join(str(v) for v in value)
        else:
            clean_fields[key] = value
    
    resp = requests.post(url, headers=AIRTABLE_HEADERS, json={"fields": clean_fields})
    if resp.status_code == 200:
        return resp.json().get("id")
    else:
        # Show error but don't stop the flow
        st.warning(f"⚠️ Could not save to Airtable (will still show matches)")
        with st.expander("See error details"):
            st.code(f"Status: {resp.status_code}\\nError: {resp.text}")
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
        score_type = 10

    # ---- Themes (0–10) ----------------------------------------------
    program_themes = as_list(
        row.get("Themes")
        or row.get("Focus_Themes")
        or row.get("Focus_Area_Themes")
        or row.get("Eligible_Themes")
    )
    program_themes_norm = {s.lower() for s in program_themes}
    proj_themes_norm = {t.lower() for t in themes} if themes else set()

    if proj_themes_norm and program_themes_norm:
        overlap = proj_themes_norm & program_themes_norm
        if overlap:
            frac = len(overlap) / len(proj_themes_norm)
            score_themes = int(10 * min(1.0, frac))
    elif not program_themes_norm:
        score_themes = 5

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
    total = min(total, 100)
    return float(total)


# ---------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------
st.set_page_config(page_title="Funding Matcher MVP", layout="wide")

# Check if we should show Grant Readiness page
if st.session_state.get('page') == 'grant_readiness':
    show_grant_readiness_page()
    st.stop()

st.markdown(
    """
    <style>
    :root {
        --bg-dark: #0b1221;
        --card: #0f172a;
        --card-alt: #1a2332;
        --muted: #9fb3c8;
        --accent: #22d3ee;
        --primary: #0f766e;
    }

    .stApp { background: radial-gradient(circle at 10% 20%, #132035 0, #0b1221 25%),
                           radial-gradient(circle at 80% 0%, rgba(34, 211, 238, 0.12), transparent 30%);
              color: #e2e8f0; }
    section.main > div { padding-top: 1rem; }
    .block-container { padding: 2rem 2.5rem 3rem; border-radius: 18px; background: rgba(15, 23, 42, 0.75); }
    textarea, input, select, .stTextInput > div > div > input, .stTextArea textarea, .stMultiSelect div[data-baseweb="input"] {
        border-radius: 12px !important;
        border: 1px solid #1f2937 !important;
        background-color: #0b1221 !important;
        color: #e2e8f0 !important;
        transition: border-color 0.2s ease;
    }
    textarea:focus, input:focus, select:focus, .stTextInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(34, 211, 238, 0.1) !important;
    }
    .stSelectbox [data-baseweb="select"] > div { border-radius: 12px !important; }
    .stMultiSelect { border-radius: 12px; }
    button[kind="primary"], .stButton button {
        border-radius: 12px;
        font-weight: 700;
        background: linear-gradient(120deg, #0f766e, #22d3ee) !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 15px rgba(34, 211, 238, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    button[kind="primary"]:hover, .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(34, 211, 238, 0.4);
    }
    .hero {
        background: linear-gradient(120deg, rgba(15, 118, 110, 0.22), rgba(34, 211, 238, 0.14));
        border: 1px solid rgba(34, 211, 238, 0.25);
        border-radius: 20px;
        padding: 18px 20px;
        margin-bottom: 1.2rem;
        box-shadow: 0 15px 40px rgba(0,0,0,0.25);
    }
    .hero h1 { margin: 0; font-size: 1.8rem; }
    .eyebrow { text-transform: uppercase; letter-spacing: 0.2em; font-size: 0.75rem; color: var(--accent); margin-bottom: 0.35rem; }
    .pill { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px; background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.08); color: #e2e8f0; font-size: 0.9rem; }
    .pill .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); display: inline-block; }

    .input-section {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }

    .section-header { display: flex; align-items: center; gap: 12px; margin: 1.5rem 0 1rem; }
    .section-number { width: 36px; height: 36px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; background: rgba(34, 211, 238, 0.16); color: #e2e8f0; font-weight: 700; }
    .section-header h3 { margin: 0; }
    .section-sub { color: var(--muted); margin-top: 2px; margin-bottom: 0; }

    .program-card {
        border-radius: 18px;
        padding: 20px 22px 14px;
        margin-bottom: 1rem;
        background: var(--card);
        border: 1px solid #1f2937;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .program-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.4);
    }
    .program-card-alt {
        background: var(--card-alt);
    }
    .program-card h3 { margin-bottom: 0.1rem; }
    .program-top { display: flex; justify-content: space-between; gap: 12px; align-items: center; flex-wrap: wrap; }
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        border-radius: 14px;
        background: linear-gradient(120deg, #0f766e, #22d3ee);
        color: #0b1221;
        font-weight: 800;
        box-shadow: 0 4px 12px rgba(34, 211, 238, 0.3);
    }
    .score-badge small { text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.7rem; opacity: 0.9; }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 12px 14px;
        border-radius: 12px;
        transition: background 0.2s ease;
    }
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.06);
    }
    .metric-label { color: var(--muted); font-size: 0.85rem; margin: 0; }
    .metric-value { font-size: 1.05rem; margin: 0.15rem 0 0; font-weight: 600; }

    .info-box {
        background: rgba(15, 118, 110, 0.08);
        border: 1px solid rgba(15, 118, 110, 0.2);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 0.75rem 0;
    }

    .muted { color: var(--muted); }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("ℹ️ About")
    st.markdown(
        """
        **EcoProject Navigator** - Funding Matcher
        
        Features:
        - Match to 48+ funding programs
        - AI Deep Dive (strategic analysis)
        - Grant Readiness (application prep)
        
        Quick test:
        """
    )
    
    # Quick test buttons for both SFI and HCTF
    if st.button("🧪 Test SFI", use_container_width=True):
        df = load_funding_programs()
        sfi = df[df['Program_Name'].str.contains('SFI', case=False, na=False)]
        if not sfi.empty:
            st.session_state['user_intake'] = {
                "organization": "Test First Nation",
                "name": "Test User",
                "email": "test@example.com",
                "applicant_type": "First Nation",
                "region": "Barkley Sound",
                "budget_range": "$250k–1M",
                "project_types": ["Forest restoration"],
                "themes": ["Climate adaptation"],
                "stage": "Planning",
                "project_title": "Cedar Enhancement",
                "description": "Restore cedar stands",
                "project_size": 500,
            }
            st.session_state['selected_program'] = sfi.iloc[0].to_dict()
            st.session_state.page = 'grant_readiness'
            st.rerun()
    
    if st.button("🧪 Test HCTF", use_container_width=True):
        df = load_funding_programs()
        hctf = df[df['Program_Name'].str.contains('Habitat Conservation|HCTF', case=False, na=False)]
        if not hctf.empty:
            st.session_state['user_intake'] = {
                "organization": "Test Conservation Group",
                "name": "Test User",
                "email": "test@example.com",
                "applicant_type": "Non-profit / Charity",
                "region": "Vancouver Island",
                "budget_range": "$50–250k",
                "project_types": ["Riparian planting", "Monitoring"],
                "themes": ["Salmon habitat", "Biodiversity"],
                "stage": "Ready to implement",
                "project_title": "Salmon Habitat Restoration",
                "description": "Restore riparian buffers for salmon",
                "project_size": 25,
            }
            st.session_state['selected_program'] = hctf.iloc[0].to_dict()
            st.session_state.page = 'grant_readiness'
            st.rerun()

st.markdown(
    """
    <div class="hero">
        <p class="eyebrow">Funding matcher MVP</p>
        <h1>EcoProject Navigator</h1>
        <p class="muted">Match your project to funding programs with AI-powered insights and application support.</p>
        <div class="pill" style="margin-top: 8px;">
            <span class="dot"></span>
            48+ programs · Deep Dive · Grant Readiness
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------- Inputs -------------------
st.markdown(
    """
    <div class="section-header">
        <div class="section-number">1</div>
        <div>
            <h3>Who are you?</h3>
            <p class="section-sub">Applicant type affects eligibility.</p>
        </div>
    </div>
    <div class="input-section">
    """,
    unsafe_allow_html=True,
)

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

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="section-header">
        <div class="section-number">2</div>
        <div>
            <h3>Project basics</h3>
            <p class="section-sub">Location, scope, and focus.</p>
        </div>
    </div>
    <div class="input-section">
    """,
    unsafe_allow_html=True,
)
col1, col2 = st.columns(2)

with col1:
    region = st.text_input("Region / Watershed")
    budget_range = st.selectbox(
        "Budget range",
        ["<$50k", "$50–250k", "$250k–1M", ">1M"],
    )
    stage = st.selectbox(
        "Project stage",
        ["Idea", "Planning", "Ready to implement", "Shovel-ready"],
    )

with col2:
    project_types = st.multiselect(
        "Project type(s)",
        [
            "Culvert replacement",
            "Road deactivation / upgrades",
            "Riparian planting",
            "Instream LWD / channel work",
            "Forest restoration",
            "Planning / assessment",
            "Monitoring",
            "Community engagement / education",
            "Land acquisition / conservation",
        ],
    )
    themes = st.multiselect(
        "Theme(s)",
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
description = st.text_area("Project description", height=120)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------------------------
# MAIN BUTTON
# ---------------------------------------------------------------------
if st.button("🔍 Find funding matches", type="primary"):

    st.session_state['user_intake'] = {
        "organization": org_name,
        "name": name,
        "email": email,
        "applicant_type": applicant_type,
        "region": region,
        "budget_range": budget_range,
        "project_types": project_types,
        "themes": themes,
        "stage": stage,
        "project_title": project_title,
        "description": description,
        "partners": partners,
    }

    # Save to Airtable (non-blocking if fails)
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

    # Load programs
    df = load_funding_programs()
    if df.empty:
        st.warning("No programs found")
        st.stop()

    # Score
    df["RawScore"] = df.apply(
        lambda row: raw_score_program(
            row, applicant_type, project_types, themes, budget_range, region, stage
        ),
        axis=1,
    )
    df["Score"] = df["RawScore"].round().astype(int)

    # Sort
    df = df.sort_values(by=["Score", "Program_Name"], ascending=[False, True], kind="mergesort")

    # Update top program
    if not df.empty and submission_id:
        update_project_submission(submission_id, {"Top Program ID": df.iloc[0]["id"]})

    st.session_state['matches'] = df

    # Display
    st.markdown(
        """
        <div class="section-header">
            <div class="section-number">3</div>
            <div>
                <h3>Your funding matches</h3>
                <p class="section-sub">Ranked by match score</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for idx, row in df.iterrows():
        program_name = row.get("Program_Name", "Unknown")
        card_class = "program-card" if idx % 2 == 0 else "program-card program-card-alt"
        
        st.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="program-top">
                <div>
                    <p class="eyebrow">Funding opportunity</p>
                    <h3>🌊 {program_name}</h3>
                </div>
                <div class="score-badge">
                    <span>{int(row['Score'])}</span>
                    <small>match</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="metric-grid">
                <div class="metric-card">
                    <p class="metric-label">Max grant</p>
                    <p class="metric-value">{row.get('Max_Grant_Amount', '—')}</p>
                </div>
                <div class="metric-card">
                    <p class="metric-label">Deadline</p>
                    <p class="metric-value">{row.get('Application_Deadline', '—')}</p>
                </div>
                <div class="metric-card">
                    <p class="metric-label">Competition</p>
                    <p class="metric-value">{row.get('Competitiveness_Level', '—')}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if row.get("Program_Description"):
            st.markdown("<div class='info-box'>", unsafe_allow_html=True)
            st.write(row["Program_Description"])
            st.markdown("</div>", unsafe_allow_html=True)

        # Buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Deep Dive", key=f"dd_{idx}"):
                st.session_state['selected_program'] = row.to_dict()
                st.info("🤖 Deep Dive triggered!")
        
        with col2:
            if has_template(program_name):
                if st.button("📋 Grant Readiness", key=f"gr_{idx}", type="primary"):
                    st.session_state['selected_program'] = row.to_dict()
                    st.session_state.page = 'grant_readiness'
                    st.rerun()
            else:
                st.button("📋 Grant Readiness", key=f"gr_{idx}", disabled=True, help="Coming soon")

        st.markdown("</div>", unsafe_allow_html=True)
