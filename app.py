import os
import urllib.parse
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from funding_templates.program_mapper import has_template
from grant_readiness_page import show_grant_readiness_page

# VERSION TRACKING
APP_VERSION = "v2.2.1"
LAST_UPDATED = "Dec 22, 2025 - 8:45 AM PST - Deep Dive persists across reruns"

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

    # Clean fields
    clean_fields = {}
    for key, value in fields.items():
        if isinstance(value, list):
            clean_fields[key] = ", ".join(str(v) for v in value)
        else:
            clean_fields[key] = value
    
    resp = requests.post(url, headers=AIRTABLE_HEADERS, json={"fields": clean_fields})
    if resp.status_code == 200:
        return resp.json().get("id")
    else:
        st.warning(f"⚠️ Could not save to Airtable (will still show matches)")
        with st.expander("See error details"):
            st.code(f"Status: {resp.status_code}\nError: {resp.text}")
        return None


def update_project_submission(record_id: str, fields: dict) -> bool:
    """Update an existing project submission record in Airtable."""
    table_name_encoded = urllib.parse.quote(PROJECTS_TABLE, safe="")
    url = f"{AIRTABLE_API_BASE}/{table_name_encoded}/{record_id}"
    resp = requests.patch(url, headers=AIRTABLE_HEADERS, json={"fields": fields})
    if resp.status_code != 200:
        st.error(f"Error updating project: {resp.status_code} – {resp.text}")
    return resp.status_code == 200


def trigger_deep_dive(submission_id: str, program_id: str, program_name: str) -> bool:
    """Update Airtable record to trigger Make.com Deep Dive automation"""
    fields = {
        "Deep Dive": program_name,  # This will trigger Make.com watch
        "Deep Dive Status": "pending",
        "Top Program ID": program_id,
    }
    
    return update_project_submission(submission_id, fields)


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
# PRD-aligned scoring
# ---------------------------------------------------------------------
def raw_score_program(row, applicant_type, project_types, themes, budget_range, region, stage):
    score_region = 0
    score_applicant = 0
    score_type = 0
    score_themes = 0
    score_budget = 0
    stage_bonus = 0

    # Region (0–30)
    elig_regions = as_list(row.get("Eligible_Regions") or row.get("Region") or row.get("Regions"))
    region_norm = (region or "").strip().lower()

    if region_norm:
        if not elig_regions:
            score_region = 15
        else:
            if any(region_norm in r.lower() or r.lower() in region_norm for r in elig_regions):
                score_region = 30
            else:
                score_region = 0
    else:
        score_region = 10

    # Applicant (0–30)
    elig_apps = as_list(row.get("Eligible_Applicants"))
    app_norm = (applicant_type or "").lower()

    if not elig_apps:
        score_applicant = 15
    elif any(app_norm in s.lower() for s in elig_apps):
        score_applicant = 30
    else:
        score_applicant = 0

    # Project type (0–20)
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

    # Themes (0–10)
    program_themes = as_list(
        row.get("Themes") or row.get("Focus_Themes") or 
        row.get("Focus_Area_Themes") or row.get("Eligible_Themes")
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

    # Budget (0–10)
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

    # Stage bonus (+5)
    program_stages = as_list(row.get("Project_Stages") or row.get("Stage_Preference") or row.get("Stages"))
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
st.set_page_config(page_title="EcoProject Navigator", layout="wide")

# Check if showing Grant Readiness page
if st.session_state.get('page') == 'grant_readiness':
    show_grant_readiness_page()
    st.stop()

st.markdown(
    """
    <style>
    :root {
        --bg-dark: #0f172a;
        --card: #1e293b;
        --card-alt: #334155;
        --muted: #94a3b8;
        --accent: #14b8a6;
        --primary: #0d9488;
    }

    .stApp { 
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f1f5f9; 
    }
    section.main > div { padding-top: 1rem; }
    .block-container { padding: 2rem 2.5rem 3rem; border-radius: 18px; background: rgba(30, 41, 59, 0.4); }
    
    textarea, input, select, .stTextInput > div > div > input, .stTextArea textarea, .stMultiSelect div[data-baseweb="input"] {
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        transition: border-color 0.2s ease;
    }
    textarea:focus, input:focus, select:focus, .stTextInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(20, 184, 166, 0.2) !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div { border-radius: 12px !important; }
    .stMultiSelect { border-radius: 12px; }
    
    button[kind="primary"], .stButton button {
        border-radius: 12px;
        font-weight: 700;
        background: linear-gradient(120deg, #0d9488, #14b8a6) !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 15px rgba(20, 184, 166, 0.4);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    button[kind="primary"]:hover, .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(20, 184, 166, 0.6);
    }
    
    .hero {
        background: linear-gradient(120deg, rgba(13, 148, 136, 0.25), rgba(20, 184, 166, 0.15));
        border: 1px solid rgba(20, 184, 166, 0.3);
        border-radius: 20px;
        padding: 18px 20px;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .hero h1 { margin: 0; font-size: 1.8rem; color: #f1f5f9; }
    .eyebrow { text-transform: uppercase; letter-spacing: 0.2em; font-size: 0.75rem; color: var(--accent); margin-bottom: 0.35rem; }
    .pill { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px; background: rgba(20, 184, 166, 0.15); border: 1px solid rgba(20, 184, 166, 0.25); color: #f1f5f9; font-size: 0.9rem; }
    .pill .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); display: inline-block; }

    .input-section {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    .section-header { display: flex; align-items: center; gap: 12px; margin: 1.5rem 0 1rem; }
    .section-number { width: 36px; height: 36px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; background: rgba(20, 184, 166, 0.2); color: #f1f5f9; font-weight: 700; }
    .section-header h3 { margin: 0; color: #f1f5f9; }
    .section-sub { color: var(--muted); margin-top: 2px; margin-bottom: 0; }

    .program-card {
        border-radius: 18px;
        padding: 20px 22px 14px;
        margin-bottom: 1rem;
        background: var(--card);
        border: 1px solid #334155;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .program-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(20, 184, 166, 0.15);
        border-color: rgba(20, 184, 166, 0.3);
    }
    .program-card-alt { background: var(--card-alt); }
    .program-card h3 { margin-bottom: 0.1rem; color: #f1f5f9; }
    .program-top { display: flex; justify-content: space-between; gap: 12px; align-items: center; flex-wrap: wrap; }
    
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        border-radius: 14px;
        background: linear-gradient(120deg, #0d9488, #14b8a6);
        color: #0f172a;
        font-weight: 800;
        box-shadow: 0 4px 12px rgba(20, 184, 166, 0.4);
    }
    .score-badge small { text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.7rem; opacity: 0.9; }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: rgba(51, 65, 85, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.15);
        padding: 12px 14px;
        border-radius: 12px;
        transition: background 0.2s ease;
    }
    .metric-card:hover { background: rgba(51, 65, 85, 0.7); }
    .metric-label { color: var(--muted); font-size: 0.85rem; margin: 0; }
    .metric-value { font-size: 1.05rem; margin: 0.15rem 0 0; font-weight: 600; color: #f1f5f9; }

    .info-box {
        background: rgba(13, 148, 136, 0.1);
        border: 1px solid rgba(20, 184, 166, 0.25);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 0.75rem 0;
    }

    .version-badge {
        background: rgba(20, 184, 166, 0.15);
        border: 1px solid rgba(20, 184, 166, 0.3);
        border-radius: 8px;
        padding: 8px 12px;
        margin-top: 20px;
        font-size: 0.75rem;
        color: #94a3b8;
    }

    .muted { color: var(--muted); }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar with VERSION
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown(
        """
        **EcoProject Navigator**
        
        Features:
        - Match to 48+ programs
        - AI Deep Dive analysis
        - Grant Readiness assessment
        """
    )
    
    # VERSION DISPLAY
    st.markdown(
        f"""
        <div class="version-badge">
            <strong>Version:</strong> {APP_VERSION}<br>
            <strong>Updated:</strong> {LAST_UPDATED}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    st.subheader("🧪 Quick Tests")
    
    if st.button("Test SFI", use_container_width=True):
        df = load_funding_programs()
        if df.empty:
            st.error("Cannot load programs")
        else:
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
    
    if st.button("Test HCTF", use_container_width=True):
        df = load_funding_programs()
        if df.empty:
            st.error("Cannot load programs")
        else:
            hctf = df[df['Program_Name'].str.contains('Habitat Conservation|HCTF', case=False, na=False)]
            if not hctf.empty:
                st.session_state['user_intake'] = {
                    "organization": "Test Conservation Group",
                    "name": "Test User",
                    "email": "test@example.com",
                    "applicant_type": "Non-profit / Charity",
                    "region": "Vancouver Island",
                    "budget_range": "$50–250k",
                    "project_types": ["Riparian planting"],
                    "themes": ["Salmon habitat"],
                    "stage": "Ready to implement",
                    "project_title": "Salmon Habitat Restoration",
                    "description": "Restore riparian buffers",
                    "project_size": 25,
                }
                st.session_state['selected_program'] = hctf.iloc[0].to_dict()
                st.session_state.page = 'grant_readiness'
                st.rerun()

# Header
st.markdown(
    """
    <div class="hero">
        <p class="eyebrow">Funding Matcher</p>
        <h1>EcoProject Navigator</h1>
        <p class="muted">Match your project to funding with AI insights and application support.</p>
        <div class="pill" style="margin-top: 8px;">
            <span class="dot"></span>
            48+ programs · Deep Dive · Grant Readiness
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Section 1: Who are you?
st.markdown(
    """
    <div class="section-header">
        <div class="section-number">1</div>
        <div>
            <h3>Who are you?</h3>
            <p class="section-sub">Applicant type affects eligibility</p>
        </div>
    </div>
    <div class="input-section">
    """,
    unsafe_allow_html=True,
)

org_name = st.text_input("Organization")
name = st.text_input("Your name")
email = st.text_input("Email")

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

partners = st.text_input("Partners (optional)")
st.markdown("</div>", unsafe_allow_html=True)

# Section 2
st.markdown(
    """
    <div class="section-header">
        <div class="section-number">2</div>
        <div>
            <h3>Project basics</h3>
            <p class="section-sub">Location, scope, and focus</p>
        </div>
    </div>
    <div class="input-section">
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    region = st.text_input("Region / Watershed")
    budget_range = st.selectbox("Budget", ["<$50k", "$50–250k", "$250k–1M", ">1M"])
    stage = st.selectbox("Stage", ["Idea", "Planning", "Ready to implement", "Shovel-ready"])

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
        "Themes",
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
description = st.text_area("Description", height=120)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

def render_matches(df: pd.DataFrame) -> None:
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

    submission_id = st.session_state.get("submission_id")

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

        st.markdown("---")
        button_col1, button_col2 = st.columns(2)
        
        with button_col1:
            if st.button(f"🔍 Deep Dive", key=f"deep_dive_{idx}", use_container_width=True):
                if submission_id:
                    success = trigger_deep_dive(submission_id, row.get("id"), program_name)
                    
                    if success:
                        user_email = st.session_state['user_intake'].get('email', 'your email')
                        st.success("✅ Deep Dive Analysis Requested!")
                        st.info(f"""
**📧 Expect email within 24 hours**

Generating strategic analysis for **{program_name}**.

Report will be sent to: **{user_email}**

Includes:
- GO/NO-GO verdict with score
- 3 immediate action items  
- Fit analysis & gaps
- Required documents
- Budget strategy
- Red flags to avoid
- 72-hour action plan

**Estimated delivery:** 2-5 minutes
                        """)
                        st.balloons()
                    else:
                        st.error("Failed to request Deep Dive - please try again")
                else:
                    st.warning("Please fill out the form first")
        
        with button_col2:
            template_exists = has_template(program_name)
            
            if template_exists:
                if st.button(
                    f"📋 Grant Readiness", 
                    key=f"grant_readiness_{idx}", 
                    type="primary",
                    use_container_width=True
                ):
                    st.session_state['selected_program'] = row.to_dict()
                    st.session_state.page = 'grant_readiness'
                    st.rerun()
            else:
                st.button(
                    f"📋 Grant Readiness",
                    key=f"grant_readiness_{idx}",
                    disabled=True,
                    help="Template coming soon",
                    use_container_width=True
                )

        st.markdown("</div>", unsafe_allow_html=True)
        
    st.success(f"✅ Showing {len(df)} programs!")


# FIND MATCHES BUTTON
if st.button("🔍 Find funding matches", type="primary", use_container_width=True):

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

    fields = {
        "Name": name,
        "Email": email,
        "Applicant Type": applicant_type,
        "Region": region,
        "Budget Range": budget_range,
        "Project Types": ", ".join(project_types) if project_types else "",
        "Project Title": project_title,
        "Description": description,
        "Stage": stage,
        "Themes": ", ".join(themes) if themes else "",
        "Partners": partners,
    }

    submission_id = create_project_submission(fields)
    if submission_id:
        st.session_state['submission_id'] = submission_id

    df = load_funding_programs()
    if df.empty:
        st.warning("No programs found")
        st.stop()

    df["RawScore"] = df.apply(
        lambda row: raw_score_program(
            row, applicant_type, project_types, themes, budget_range, region, stage
        ),
        axis=1,
    )
    df["Score"] = df["RawScore"].round().astype(int)
    df = df.sort_values(by=["Score", "Program_Name"], ascending=[False, True], kind="mergesort")

    if not df.empty and submission_id:
        update_project_submission(submission_id, {"Top Program ID": df.iloc[0]["id"]})

    st.session_state['matches'] = df

matches = st.session_state.get("matches")
if matches is not None and not matches.empty:
    render_matches(matches)
