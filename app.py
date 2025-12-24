import os
import urllib.parse
import requests
import streamlit as st
import pandas as pd
import html
from dotenv import load_dotenv
from funding_templates.program_mapper import has_template
from grant_readiness_page import show_grant_readiness_page
from datetime import datetime, timedelta

APP_VERSION = "v2.6.2"
LAST_UPDATED = "Dec 24, 2025 - 5:00 PM PST - Enhanced dropdown autofill blocking"

load_dotenv()
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT") or st.secrets.get("AIRTABLE_PAT")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID") or st.secrets.get("AIRTABLE_BASE_ID", "appZvlRCnU5NencKj")
FUNDING_TABLE = os.getenv("AIRTABLE_FUNDING_TABLE") or st.secrets.get("AIRTABLE_FUNDING_TABLE", "Funding Programs")
PROJECTS_TABLE = os.getenv("AIRTABLE_PROJECTS_TABLE") or st.secrets.get("AIRTABLE_PROJECTS_TABLE", "Project Submissions")
AIRTABLE_API_BASE = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}"
AIRTABLE_HEADERS = {"Authorization": f"Bearer {AIRTABLE_PAT}", "Content-Type": "application/json"}

def create_project_submission(fields: dict) -> str | None:
    table_name_encoded = urllib.parse.quote(PROJECTS_TABLE, safe="")
    url = f"{AIRTABLE_API_BASE}/{table_name_encoded}"
    clean_fields = {k: (", ".join(str(v) for v in val) if isinstance(val, list) else str(val)) for k, val in fields.items() if val and val != "Select..."}
    resp = requests.post(url, headers=AIRTABLE_HEADERS, json={"fields": clean_fields})
    return resp.json().get("id") if resp.status_code == 200 else None

def update_project_submission(record_id: str, fields: dict) -> bool:
    table_name_encoded = urllib.parse.quote(PROJECTS_TABLE, safe="")
    return requests.patch(f"{AIRTABLE_API_BASE}/{table_name_encoded}/{record_id}", headers=AIRTABLE_HEADERS, json={"fields": fields}).status_code == 200

def trigger_deep_dive(submission_id: str, program_id: str, program_name: str) -> bool:
    return update_project_submission(submission_id, {"Deep Dive": program_name, "Deep Dive Status": "pending ", "Top Program ID": program_id})

@st.cache_data(ttl=300)
def load_funding_programs() -> pd.DataFrame:
    table_name_encoded = urllib.parse.quote(FUNDING_TABLE, safe="")
    url = f"{AIRTABLE_API_BASE}/{table_name_encoded}"
    all_records, offset, page_count = [], None, 0
    while True:
        page_count += 1
        resp = requests.get(url, headers=AIRTABLE_HEADERS, params={"offset": offset} if offset else {})
        if resp.status_code != 200 or page_count > 10:
            break
        data = resp.json()
        for rec in data.get("records", []):
            fields = rec.get("fields", {})
            fields["id"] = rec.get("id")
            all_records.append(fields)
        offset = data.get("offset")
        if not offset:
            break
    return pd.DataFrame(all_records)

def as_list(value):
    return [str(v) for v in value] if isinstance(value, list) else ([value] if isinstance(value, str) else [])

def parse_number(value):
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("$", "")) if isinstance(value, str) else None
    except:
        return None

def estimate_project_budget(band: str) -> float | None:
    return {"<$50k": 25_000, "$50–250k": 150_000, "$250k–1M": 500_000, ">1M": 1_500_000}.get(band)

def parse_deadline(deadline_str: str) -> int:
    if not deadline_str or deadline_str == "—" or "rolling" in deadline_str.lower():
        return 999
    try:
        for fmt in ["%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y"]:
            try:
                return max(0, (datetime.strptime(deadline_str.strip(), fmt) - datetime.now()).days)
            except:
                continue
    except:
        pass
    return 999

def check_keyword_match(user_text: str, program_name: str, funder_name: str) -> int:
    if not user_text:
        return 0
    user_text_lower = user_text.lower()
    score = 0
    if program_name:
        for word in program_name.split():
            if len(word) <= 6 and word.isupper() and word.lower() in user_text_lower:
                score += 15
                break
        program_words = program_name.lower().split()
        if len(program_words) >= 3:
            for i in range(len(program_words) - 2):
                phrase = " ".join(program_words[i:i+3])
                if len(phrase) > 12 and phrase in user_text_lower:
                    score += 12
                    break
        for term in ["climate smart", "habitat conservation", "watershed security", "salmon resiliency"]:
            if term in program_name.lower() and term in user_text_lower:
                score += 8
    if funder_name and len(funder_name) > 3 and funder_name.lower() in user_text_lower:
        score += 7
    return min(score, 25)

def raw_score_program(row, applicant_type, project_types, themes, budget_range, region, stage, project_title, description, partners):
    s = [0] * 5
    elig_regions = as_list(row.get("Eligible_Regions") or row.get("Region"))
    region_norm = (region or "").strip().lower()
    s[0] = 8 if not region_norm else (12 if not elig_regions else (20 if any(region_norm in r.lower() or r.lower() in region_norm for r in elig_regions) else 0))
    elig_apps = as_list(row.get("Eligible_Applicants"))
    s[1] = 15 if not elig_apps else (30 if any((applicant_type or "").lower() in a.lower() for a in elig_apps) else 0)
    elig_types = {t.lower() for t in as_list(row.get("Eligible_Project_Types") or row.get("Focus_Area"))}
    proj_types_set = {pt.lower() for pt in project_types} if project_types else set()
    s[2] = (int(20 * min(1.0, len(proj_types_set & elig_types) / len(proj_types_set))) if (proj_types_set & elig_types) else 0) if proj_types_set and elig_types else (10 if not elig_types else 0)
    prog_themes = {t.lower() for t in as_list(row.get("Themes") or row.get("Eligible_Themes"))}
    user_themes_set = {t.lower() for t in themes} if themes else set()
    s[3] = (int(15 * min(1.0, len(user_themes_set & prog_themes) / len(user_themes_set))) if (user_themes_set & prog_themes) else 0) if user_themes_set and prog_themes else (7 if not prog_themes else 0)
    proj_budget, max_amt = estimate_project_budget(budget_range), parse_number(row.get("Max_Grant_Amount"))
    s[4] = 5 if not proj_budget or not max_amt else (10 if proj_budget <= max_amt else (5 if proj_budget <= 1.5 * max_amt else 0))
    bonuses = (5 if (stage or "").lower() and any((stage or "").lower() in st.lower() for st in as_list(row.get("Project_Stages") or row.get("Stage_Preference"))) else 0)
    bonuses += check_keyword_match(f"{project_title or ''} {description or ''}".strip(), row.get("Program_Name", ""), row.get("Funder_Organization", ""))
    days = parse_deadline(row.get("Application_Deadline", ""))
    bonuses += 3 if days > 90 else (2 if days > 30 else (-5 if days < 14 else 0))
    bonuses += 3 if user_themes_set and any(t in ["salmon habitat", "watershed health"] for t in user_themes_set) else 0
    bonuses += 4 if "first nation" in (partners or "").lower() or "indigenous" in (partners or "").lower() or applicant_type in ["First Nation", "Indigenous organization"] else 0
    return float(min(sum(s) + bonuses, 100))

st.set_page_config(page_title="EcoProject Navigator", layout="wide")

if st.session_state.get('page') == 'grant_readiness':
    show_grant_readiness_page()
    st.stop()

st.markdown("""<style>
:root{--card:#475569;--text:#f8fafc;--muted:#cbd5e1;--accent:#14b8a6;--bright:#5eead4}
.stApp{background:linear-gradient(135deg,#1e293b,#334155);color:var(--text)}
.block-container{padding:2rem 3rem;background:rgba(51,65,85,0.3);border-radius:20px}
textarea,input,select,.stTextInput input,.stTextArea textarea,.stSelectbox select,.stMultiSelect>div>div{background:#475569!important;border:2px solid #64748b!important;border-radius:10px!important;color:#f8fafc!important;padding:12px!important}
textarea:focus,input:focus,select:focus{border-color:var(--bright)!important;box-shadow:0 0 0 3px rgba(94,234,212,0.2)!important}
input:-webkit-autofill,input:-webkit-autofill:hover,input:-webkit-autofill:focus{-webkit-box-shadow:0 0 0 30px #475569 inset!important;-webkit-text-fill-color:#f8fafc!important}

/* Enhanced: Hide ALL autofill/placeholder elements in selectbox */
.stSelectbox > div > div > div[data-baseweb="select"] > div:first-child,
.stSelectbox [data-baseweb="popover"] > div:first-child,
.stSelectbox div[class*="placeholder"],
.stSelectbox div[data-baseweb="tag"],
.stSelectbox svg[data-baseweb="icon"]:first-of-type,
.stSelectbox [class*="Svg"],
.stSelectbox [class*="ValueContainer"] > div:first-child:not([class*="Input"]),
div[data-baseweb="select"] [class*="singleValue"]:empty,
div[data-baseweb="select"] > div:first-child > div:first-child {
    display:none!important;
    visibility:hidden!important;
    opacity:0!important;
    width:0!important;
    height:0!important;
}

/* Ensure placeholder text shows correctly */
.stSelectbox input[type="text"]::placeholder {
    color: #94a3b8!important;
    opacity: 1!important;
}

.stButton button{background:linear-gradient(120deg,#14b8a6,#5eead4)!important;color:#0f172a!important;font-weight:700!important;border-radius:12px!important;padding:14px 28px!important;border:none!important;box-shadow:0 4px 20px rgba(94,234,212,0.5);transition:all .3s}
.stButton button:hover{transform:translateY(-3px) scale(1.02);box-shadow:0 8px 30px rgba(94,234,212,0.7)}

.hero{
    background:linear-gradient(rgba(30,41,59,0.45),rgba(15,23,42,0.65)),url(https://raw.githubusercontent.com/davidbeleznay/FundMatching/main/hero-background.jpg);
    background-size:cover;
    background-position:center;
    border:2px solid rgba(94,234,212,0.5);
    border-radius:20px;
    padding:56px 36px;
    margin-bottom:2rem;
    box-shadow:0 12px 50px rgba(20,184,166,0.4)
}
.hero h1{margin:0;font-size:2.8rem;color:#ffffff;text-shadow:0 3px 25px rgba(0,0,0,0.9),0 1px 3px rgba(0,0,0,0.8);font-weight:800}
.hero .eyebrow{text-shadow:0 2px 15px rgba(0,0,0,0.8);color:#5eead4}
.hero .pill{background:rgba(15,23,42,0.85);backdrop-filter:blur(12px);border:1px solid rgba(94,234,212,0.4)}
.hero p{text-shadow:0 2px 15px rgba(0,0,0,0.8)}

.input-section{background:rgba(71,85,105,0.4);border:1px solid rgba(203,213,225,0.2);border-radius:16px;padding:24px;margin-bottom:2rem}
.section-number{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#14b8a6,#5eead4);color:#0f172a;font-weight:800;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 4px 15px rgba(94,234,212,0.4)}
.program-card{background:#475569;border:2px solid #64748b;border-radius:16px;padding:24px;margin-bottom:1.5rem;box-shadow:0 8px 25px rgba(0,0,0,0.2);transition:all .3s}
.program-card:hover{transform:translateY(-5px);box-shadow:0 15px 40px rgba(94,234,212,0.3);border-color:var(--bright)}
.program-card h3{color:#f8fafc}
.score-badge{background:linear-gradient(120deg,#14b8a6,#5eead4);color:#0f172a;font-weight:800;padding:14px 20px;border-radius:14px;box-shadow:0 4px 15px rgba(94,234,212,0.5)}
.metric-card{background:rgba(71,85,105,0.6);border:1px solid rgba(203,213,225,0.2);padding:14px;border-radius:12px}
.metric-value{color:#f8fafc;font-weight:700}
.info-box{background:rgba(20,184,166,0.15);border:1px solid rgba(94,234,212,0.3);border-radius:12px;padding:16px;color:#f8fafc!important}
.version-badge{background:rgba(94,234,212,0.2);border:1px solid rgba(94,234,212,0.4);border-radius:8px;padding:10px 14px;margin-top:20px;font-size:0.75rem}
.eyebrow{color:var(--bright);text-transform:uppercase;letter-spacing:.15em;font-size:.75rem;font-weight:600}
.pill{background:rgba(94,234,212,0.2);border:1px solid rgba(94,234,212,0.3);padding:8px 14px;border-radius:999px;display:inline-flex;align-items:center;gap:8px}
.pill .dot{width:8px;height:8px;background:var(--bright);border-radius:50%;box-shadow:0 0 8px var(--bright)}
.section-header{display:flex;align-items:center;gap:15px;margin:2rem 0 1rem}
.section-header h3{margin:0;color:#f8fafc;font-size:1.5rem}
.section-sub{color:var(--muted);margin-top:4px}
.metric-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin:1rem 0}
.metric-label{color:var(--muted);font-size:.85rem}
.program-top{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap;margin-bottom:1rem}
.keyword-badge{background:rgba(251,191,36,0.35);border:2px solid rgba(251,191,36,0.7);color:#fcd34d;padding:6px 14px;border-radius:8px;font-size:0.8rem;font-weight:800;margin-left:10px;text-transform:uppercase;letter-spacing:0.08em;box-shadow:0 3px 10px rgba(251,191,36,0.4)}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("**EcoProject Navigator**\n\n- Keyword matching (+25)\n- AI Deep Dive\n- Grant Readiness")
    df_count = load_funding_programs()
    if not df_count.empty:
        st.info(f"📊 {len(df_count)} programs")
    st.markdown(f'<div class="version-badge"><strong>{APP_VERSION}</strong><br>{LAST_UPDATED}</div>', unsafe_allow_html=True)
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown('<div class="hero"><p class="eyebrow">BC Environmental Funding</p><h1>🌲 EcoProject Navigator</h1><p style="color:#f8fafc;margin-top:10px;font-size:1.15rem;">Match your project to funding opportunities</p><div class="pill" style="margin-top:18px;"><span class="dot"></span>Smart keyword matching · Deep analysis</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-header"><div class="section-number">1</div><div><h3>Who are you?</h3><p class="section-sub">Required for matching</p></div></div><div class="input-section">', unsafe_allow_html=True)

# Initialize session state
if 'form_name' not in st.session_state:
    st.session_state.form_name = ""
if 'form_email' not in st.session_state:
    st.session_state.form_email = ""

org_name = st.text_input("Organization", placeholder="e.g., Pacheedaht First Nation")
name_input = st.text_input("Your name", value=st.session_state.form_name, placeholder="e.g., Sarah Johnson", key="name_widget", on_change=lambda: setattr(st.session_state, 'form_name', st.session_state.name_widget))
email_input = st.text_input("Email", value=st.session_state.form_email, placeholder="e.g., sarah@example.com", key="email_widget", on_change=lambda: setattr(st.session_state, 'form_email', st.session_state.email_widget))
applicant_type = st.selectbox("Applicant type", ["Select...", "First Nation", "Indigenous organization", "Municipality / Regional District", "Non-profit / Charity", "For-profit business", "University / Research institute", "Other"])
partners = st.text_input("Partners (optional)", placeholder="e.g., First Nation partners")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-header"><div class="section-number">2</div><div><h3>Project basics</h3><p class="section-sub">💡 Mention programs (SFI, HCTF) for +25 boost</p></div></div><div class="input-section">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    region = st.text_input("Region / Watershed", placeholder="e.g., Barkley Sound")
    budget_range = st.selectbox("Budget", ["Select...", "<$50k", "$50–250k", "$250k–1M", ">1M"])
    stage = st.selectbox("Stage", ["Select...", "Idea", "Planning", "Ready to implement", "Shovel-ready"])
with col2:
    project_types = st.multiselect("Project type(s)", ["Culvert replacement", "Road deactivation / upgrades", "Riparian planting", "Instream LWD / channel work", "Forest restoration", "Planning / assessment", "Monitoring", "Community engagement / education", "Land acquisition / conservation"])
    themes = st.multiselect("Themes", ["Climate adaptation", "Salmon habitat", "Watershed health", "Flood resilience", "Wildfire resilience", "Forest roads & access", "Erosion & sediment", "Water quality", "Biodiversity", "Wetlands & beavers", "Drinking water protection", "Community engagement / stewardship"])
project_title = st.text_input("Project title", placeholder="e.g., Climate Smart Forestry")
description = st.text_area("Description", height=120, placeholder="Mention funders (SFI, HCTF) for better matches...")
st.markdown("</div><hr>", unsafe_allow_html=True)

def render_matches(df):
    st.markdown('<div class="section-header"><div class="section-number">3</div><div><h3>Matches</h3><p class="section-sub">Keyword = +25 pts</p></div></div>', unsafe_allow_html=True)
    submission_id = st.session_state.get("submission_id")
    for idx, row in df.iterrows():
        program_name = row.get("Program_Name", "Unknown")
        user_text = f"{st.session_state.get('user_intake', {}).get('project_title', '')} {st.session_state.get('user_intake', {}).get('description', '')}".lower()
        keyword_score = check_keyword_match(user_text, program_name, row.get("Funder_Organization", ""))
        st.markdown('<div class="program-card">', unsafe_allow_html=True)
        keyword_badge = f'<span class="keyword-badge">🎯 +{keyword_score}</span>' if keyword_score > 0 else ''
        st.markdown(f'<div class="program-top"><div><p class="eyebrow">Funding</p><h3>🐟 {html.escape(program_name)}{keyword_badge}</h3></div><div class="score-badge"><span style="font-size:1.4rem;">{int(row["Score"])}</span><small style="margin-left:4px;">fit</small></div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-grid"><div class="metric-card"><p class="metric-label">Max</p><p class="metric-value">{row.get("Max_Grant_Amount","—")}</p></div><div class="metric-card"><p class="metric-label">Deadline</p><p class="metric-value">{row.get("Application_Deadline","—")}</p></div><div class="metric-card"><p class="metric-label">Competition</p><p class="metric-value">{row.get("Competitiveness_Level","—")}</p></div></div>', unsafe_allow_html=True)
        desc = row.get("Program_Description")
        if desc and str(desc).strip() and str(desc) != "nan":
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            clean_desc = html.escape(str(desc)[:500])
            st.markdown(f'<p style="color:#f8fafc;margin:0">{clean_desc}</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💧 Deep Dive", key=f"dd_{idx}", use_container_width=True):
                if submission_id and trigger_deep_dive(submission_id, row.get("id"), program_name):
                    st.success("✅ Deep Dive Analysis Requested!")
                    st.info(f'📧 **Strategic Brief Incoming**\n\nProgram: **{program_name}**\n\nYour customized analysis will be emailed to **{st.session_state["user_intake"].get("email")}** within 2-3 minutes.\n\n**What you\'ll get:**\n✓ GO/NO-GO Verdict\n✓ Critical Red Flags\n✓ Fit Analysis & Positioning\n✓ Required Documents Checklist  \n✓ Scoring Strategy\n✓ Budget Guidance\n✓ 72-Hour Action Plan\n✓ Partnership Recommendations')
                    st.markdown("""<script>const s=document.createElement('style');s.textContent='@keyframes b{0%{bottom:-50px;opacity:1}100%{bottom:100vh;opacity:0}}.bubble{position:fixed;background:radial-gradient(circle,#5eead4,#14b8a6);border-radius:50%;animation:b 5s ease-in infinite;z-index:9999;pointer-events:none}';document.head.appendChild(s);for(let i=0;i<10;i++){const e=document.createElement('div');e.className='bubble';const z=Math.random()*12+6;e.style.width=e.style.height=z+'px';e.style.left=Math.random()*100+'%';e.style.animationDelay=Math.random()*2+'s';e.style.animationDuration=(Math.random()*2+4)+'s';document.body.appendChild(e);setTimeout(()=>e.remove(),6000)}</script>""", unsafe_allow_html=True)
                else:
                    st.warning("Fill form" if not submission_id else "Failed")
        with c2:
            if has_template(program_name):
                if st.button("📋 Grant Readiness", key=f"gr_{idx}", type="primary", use_container_width=True):
                    st.session_state.update({'selected_program': row.to_dict(), 'page': 'grant_readiness'})
                    st.rerun()
            else:
                st.button("📋 Grant Readiness", key=f"gr_{idx}", disabled=True, help="Soon", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.success(f"✅ {len(df)} programs!")

if st.button("🔍 Find funding matches", type="primary", use_container_width=True):
    final_name = st.session_state.form_name.strip() or name_input.strip()
    final_email = st.session_state.form_email.strip() or email_input.strip()
    if not applicant_type or applicant_type == "Select...":
        st.error("⚠️ Select applicant type")
        st.stop()
    if not final_name:
        st.error("⚠️ Enter name")
        st.stop()
    if not final_email or "@" not in final_email:
        st.error("⚠️ Enter valid email")
        st.stop()
    st.session_state['user_intake'] = {"organization": org_name, "name": final_name, "email": final_email, "applicant_type": applicant_type, "region": region, "budget_range": budget_range, "project_types": project_types, "themes": themes, "stage": stage, "project_title": project_title, "description": description, "partners": partners}
    submission_id = create_project_submission({"Organization": org_name or f"{applicant_type} Org", "Name": final_name, "Email": final_email, "Applicant Type": applicant_type, "Region": region or "BC", "Budget Range": budget_range, "Project Types": ", ".join(project_types) if project_types else "", "Project Title": project_title or "Project", "Description": description, "Stage": stage, "Themes": ", ".join(themes) if themes else "", "Partners": partners})
    if submission_id:
        st.session_state['submission_id'] = submission_id
        st.success(f"✅ Saved: {final_name}")
    else:
        st.stop()
    df = load_funding_programs()
    if df.empty:
        st.warning("No programs")
        st.stop()
    df["RawScore"] = df.apply(lambda r: raw_score_program(r, applicant_type, project_types, themes, budget_range, region, stage, project_title, description, partners), axis=1)
    df["Score"] = df["RawScore"].round().astype(int)
    df = df.sort_values(by=["Score", "Program_Name"], ascending=[False, True])
    if not df.empty and submission_id:
        update_project_submission(submission_id, {"Top Program ID": df.iloc[0]["id"]})
    st.session_state['matches'] = df

if st.session_state.get("matches") is not None and not st.session_state["matches"].empty:
    render_matches(st.session_state["matches"])
