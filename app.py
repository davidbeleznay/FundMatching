import os
import urllib.parse
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from funding_templates.program_mapper import has_template
from grant_readiness_page import show_grant_readiness_page
from datetime import datetime, timedelta

APP_VERSION = "v2.4.0"
LAST_UPDATED = "Dec 22, 2025 - 8:40 PM PST - Enhanced scoring with keyword matching"

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
    clean_fields = {}
    for key, value in fields.items():
        if value:
            clean_fields[key] = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
    resp = requests.post(url, headers=AIRTABLE_HEADERS, json={"fields": clean_fields})
    if resp.status_code == 200:
        return resp.json().get("id")
    st.error(f"⚠️ Save failed: {resp.status_code}")
    with st.expander("Details"):
        st.code(resp.text)
    return None

def update_project_submission(record_id: str, fields: dict) -> bool:
    table_name_encoded = urllib.parse.quote(PROJECTS_TABLE, safe="")
    url = f"{AIRTABLE_API_BASE}/{table_name_encoded}/{record_id}"
    resp = requests.patch(url, headers=AIRTABLE_HEADERS, json={"fields": fields})
    return resp.status_code == 200

def trigger_deep_dive(submission_id: str, program_id: str, program_name: str) -> bool:
    return update_project_submission(submission_id, {"Deep Dive": program_name, "Deep Dive Status": "pending ", "Top Program ID": program_id})

def load_funding_programs() -> pd.DataFrame:
    table_name_encoded = urllib.parse.quote(FUNDING_TABLE, safe="")
    url = f"{AIRTABLE_API_BASE}/{table_name_encoded}"
    records, offset = [], None
    while True:
        resp = requests.get(url, headers=AIRTABLE_HEADERS, params={"offset": offset} if offset else {})
        if resp.status_code != 200:
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
    return [str(v) for v in value] if isinstance(value, list) else ([value] if isinstance(value, str) else [])

def parse_number(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").replace("$", ""))
        except:
            return None
    return None

def estimate_project_budget(band: str) -> float | None:
    return {"<$50k": 25_000, "$50–250k": 150_000, "$250k–1M": 500_000, ">1M": 1_500_000}.get(band)

def parse_deadline(deadline_str: str) -> int:
    """Parse deadline and return days until deadline (or 999 if unknown)"""
    if not deadline_str or deadline_str == "—" or "rolling" in deadline_str.lower() or "ongoing" in deadline_str.lower():
        return 999  # Treat rolling/ongoing as always open
    try:
        # Try common formats
        for fmt in ["%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y"]:
            try:
                deadline = datetime.strptime(deadline_str.strip(), fmt)
                days_until = (deadline - datetime.now()).days
                return max(0, days_until)  # Don't return negative
            except:
                continue
    except:
        pass
    return 999  # Unknown deadline

def check_keyword_match(user_text: str, program_name: str, funder_name: str) -> int:
    """
    Check if user's project title/description mentions the program/funder by name
    Returns bonus points (0-15)
    """
    if not user_text:
        return 0
    
    user_text_lower = user_text.lower()
    score = 0
    
    # Extract key program identifiers
    program_keywords = []
    
    # Direct program name match
    if program_name:
        # Split program name into meaningful chunks
        words = program_name.lower().split()
        # Add acronyms (e.g., "SFI", "HCTF", "BCSRIF")
        acronyms = [w for w in words if w.isupper() or len(w) <= 5]
        program_keywords.extend(acronyms)
        
        # Add distinctive phrases (3+ words together)
        if len(words) >= 3:
            for i in range(len(words) - 2):
                phrase = " ".join(words[i:i+3])
                if len(phrase) > 10:  # Meaningful phrases only
                    program_keywords.append(phrase)
    
    # Add funder name
    if funder_name:
        program_keywords.append(funder_name.lower())
    
    # Check for matches
    for keyword in program_keywords:
        if keyword and len(keyword) > 2 and keyword in user_text_lower:
            score += 5  # +5 per keyword match
    
    # Cap at 15 bonus points
    return min(score, 15)

def raw_score_program(row, applicant_type, project_types, themes, budget_range, region, stage, project_title, description, partners):
    """
    Enhanced scoring algorithm v2.4
    
    Base scoring (100 points):
    - Region: 25 points
    - Applicant: 30 points  
    - Project Type: 20 points
    - Themes: 15 points (INCREASED from 10)
    - Budget: 10 points
    
    Bonuses (up to +30):
    - Stage match: +5
    - Keyword match: +15 (NEW!)
    - Deadline >90 days: +3
    - Salmon/Watershed theme: +3
    - Indigenous partnership: +4
    """
    score_region = score_applicant = score_type = score_themes = score_budget = 0
    bonus_stage = bonus_keyword = bonus_deadline = bonus_salmon = bonus_indigenous = 0
    
    # REGION (0-25, reduced from 30)
    elig_regions = as_list(row.get("Eligible_Regions") or row.get("Region"))
    region_norm = (region or "").strip().lower()
    if region_norm:
        if not elig_regions:
            score_region = 12  # Reduced from 15
        else:
            if any(region_norm in r.lower() or r.lower() in region_norm for r in elig_regions):
                score_region = 25
            else:
                score_region = 0
    else:
        score_region = 8
    
    # APPLICANT (0-30, unchanged - most critical)
    elig_apps = as_list(row.get("Eligible_Applicants"))
    app_norm = (applicant_type or "").lower()
    if not elig_apps:
        score_applicant = 15
    elif any(app_norm in a.lower() for a in elig_apps):
        score_applicant = 30
    else:
        score_applicant = 0
    
    # PROJECT TYPE (0-20, unchanged)
    elig_types = {t.lower() for t in as_list(row.get("Eligible_Project_Types") or row.get("Focus_Area"))}
    proj_types_set = {pt.lower() for pt in project_types} if project_types else set()
    if proj_types_set and elig_types:
        overlap = proj_types_set & elig_types
        score_type = int(20 * min(1.0, len(overlap) / len(proj_types_set))) if overlap else 0
    elif not elig_types:
        score_type = 10
    
    # THEMES (0-15, INCREASED from 10)
    prog_themes = {t.lower() for t in as_list(row.get("Themes") or row.get("Eligible_Themes"))}
    user_themes_set = {t.lower() for t in themes} if themes else set()
    if user_themes_set and prog_themes:
        overlap = user_themes_set & prog_themes
        score_themes = int(15 * min(1.0, len(overlap) / len(user_themes_set))) if overlap else 0
    elif not prog_themes:
        score_themes = 7
    
    # BUDGET (0-10, unchanged)
    proj_budget = estimate_project_budget(budget_range)
    max_amt = parse_number(row.get("Max_Grant_Amount"))
    if not proj_budget or not max_amt:
        score_budget = 5
    else:
        score_budget = 10 if proj_budget <= max_amt else (5 if proj_budget <= 1.5 * max_amt else 0)
    
    # BONUS: Stage match (+5)
    stages = as_list(row.get("Project_Stages") or row.get("Stage_Preference"))
    if (stage or "").lower() and stages and any((stage or "").lower() in s.lower() for s in stages):
        bonus_stage = 5
    
    # BONUS: Keyword matching (+15) - NEW!
    program_name = row.get("Program_Name", "")
    funder_name = row.get("Funder_Organization", "")
    user_text = f"{project_title or ''} {description or ''}".strip()
    bonus_keyword = check_keyword_match(user_text, program_name, funder_name)
    
    # BONUS: Deadline urgency (+3)
    deadline_str = row.get("Application_Deadline", "")
    days_until = parse_deadline(deadline_str)
    if days_until > 90:  # More than 3 months to prepare
        bonus_deadline = 3
    elif days_until > 30:  # 1-3 months
        bonus_deadline = 2
    elif days_until < 14:  # Less than 2 weeks - penalty!
        bonus_deadline = -5
    
    # BONUS: Salmon/Watershed priority (+3)
    if user_themes_set and any(t in ["salmon habitat", "watershed health"] for t in user_themes_set):
        bonus_salmon = 3
    
    # BONUS: Indigenous partnership (+4)
    partners_lower = (partners or "").lower()
    if "first nation" in partners_lower or "indigenous" in partners_lower or applicant_type in ["First Nation", "Indigenous organization"]:
        bonus_indigenous = 4
    
    total_base = score_region + score_applicant + score_type + score_themes + score_budget
    total_bonus = bonus_stage + bonus_keyword + bonus_deadline + bonus_salmon + bonus_indigenous
    final_score = total_base + total_bonus
    
    return float(min(final_score, 100))

st.set_page_config(page_title="EcoProject Navigator", layout="wide")

if st.session_state.get('page') == 'grant_readiness':
    show_grant_readiness_page()
    st.stop()

st.markdown("""<style>:root{--card:#475569;--text:#f8fafc;--muted:#cbd5e1;--accent:#14b8a6;--bright:#5eead4}.stApp{background:linear-gradient(135deg,#1e293b,#334155);color:var(--text)}.block-container{padding:2rem 3rem;background:rgba(51,65,85,0.3);border-radius:20px}textarea,input,select,.stTextInput input,.stTextArea textarea{background:#475569!important;border:2px solid #64748b!important;border-radius:10px!important;color:#f8fafc!important;padding:12px!important}textarea:focus,input:focus,select:focus{border-color:var(--bright)!important;box-shadow:0 0 0 3px rgba(94,234,212,0.2)!important}.stButton button{background:linear-gradient(120deg,#14b8a6,#5eead4)!important;color:#0f172a!important;font-weight:700!important;border-radius:12px!important;padding:14px 28px!important;border:none!important;box-shadow:0 4px 20px rgba(94,234,212,0.5);transition:all .3s}.stButton button:hover{transform:translateY(-3px) scale(1.02);box-shadow:0 8px 30px rgba(94,234,212,0.7)}.hero{background:linear-gradient(120deg,rgba(20,184,166,0.3),rgba(94,234,212,0.2));border:2px solid rgba(94,234,212,0.4);border-radius:20px;padding:24px;margin-bottom:2rem;box-shadow:0 10px 40px rgba(20,184,166,0.3)}.hero h1{margin:0;font-size:2rem;color:#f8fafc;text-shadow:0 2px 10px rgba(0,0,0,0.3)}.input-section{background:rgba(71,85,105,0.4);border:1px solid rgba(203,213,225,0.2);border-radius:16px;padding:24px;margin-bottom:2rem}.section-number{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#14b8a6,#5eead4);color:#0f172a;font-weight:800;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 4px 15px rgba(94,234,212,0.4)}.program-card{background:#475569;border:2px solid #64748b;border-radius:16px;padding:24px;margin-bottom:1.5rem;box-shadow:0 8px 25px rgba(0,0,0,0.2);transition:all .3s}.program-card:hover{transform:translateY(-5px);box-shadow:0 15px 40px rgba(94,234,212,0.3);border-color:var(--bright)}.program-card h3{color:#f8fafc}.score-badge{background:linear-gradient(120deg,#14b8a6,#5eead4);color:#0f172a;font-weight:800;padding:14px 20px;border-radius:14px;box-shadow:0 4px 15px rgba(94,234,212,0.5)}.metric-card{background:rgba(71,85,105,0.6);border:1px solid rgba(203,213,225,0.2);padding:14px;border-radius:12px}.metric-value{color:#f8fafc;font-weight:700}.info-box{background:rgba(20,184,166,0.15);border:1px solid rgba(94,234,212,0.3);border-radius:12px;padding:16px}.version-badge{background:rgba(94,234,212,0.2);border:1px solid rgba(94,234,212,0.4);border-radius:8px;padding:10px 14px;margin-top:20px;font-size:0.75rem}.eyebrow{color:var(--bright);text-transform:uppercase;letter-spacing:.15em;font-size:.75rem;font-weight:600}.pill{background:rgba(94,234,212,0.2);border:1px solid rgba(94,234,212,0.3);padding:8px 14px;border-radius:999px;display:inline-flex;align-items:center;gap:8px}.pill .dot{width:8px;height:8px;background:var(--bright);border-radius:50%;box-shadow:0 0 8px var(--bright)}.section-header{display:flex;align-items:center;gap:15px;margin:2rem 0 1rem}.section-header h3{margin:0;color:#f8fafc;font-size:1.5rem}.section-sub{color:var(--muted);margin-top:4px}.metric-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin:1rem 0}.metric-label{color:var(--muted);font-size:.85rem;margin-bottom:4px}.program-top{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap;margin-bottom:1rem}.keyword-badge{background:rgba(251,191,36,0.2);border:1px solid rgba(251,191,36,0.4);color:#fbbf24;padding:4px 10px;border-radius:6px;font-size:0.75rem;font-weight:600;margin-left:8px}</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("**EcoProject Navigator**\n\n- 48+ BC programs\n- AI Deep Dive\n- Grant Readiness\n\n**New in v2.4:**\n- Keyword matching\n- Deadline scoring\n- Theme priority")
    st.markdown(f'<div class="version-badge"><strong>{APP_VERSION}</strong><br>{LAST_UPDATED}</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🧪 Quick Tests")
    if st.button("Test SFI", use_container_width=True):
        df = load_funding_programs()
        if not df.empty:
            sfi = df[df['Program_Name'].str.contains('SFI', case=False, na=False)]
            if not sfi.empty:
                st.session_state.update({'user_intake': {"organization": "Test FN", "name": "Test User", "email": "test@example.com", "applicant_type": "First Nation", "region": "Barkley Sound", "budget_range": "$250k–1M", "project_types": ["Forest restoration"], "themes": ["Climate adaptation"], "stage": "Planning", "project_title": "Cedar Enhancement", "description": "Restore cedar"}, 'selected_program': sfi.iloc[0].to_dict(), 'page': 'grant_readiness'})
                st.rerun()
    if st.button("Test HCTF", use_container_width=True):
        df = load_funding_programs()
        if not df.empty:
            hctf = df[df['Program_Name'].str.contains('Habitat|HCTF', case=False, na=False)]
            if not hctf.empty:
                st.session_state.update({'user_intake': {"organization": "Test Group", "name": "Test User", "email": "test@example.com", "applicant_type": "Non-profit / Charity", "region": "Vancouver Island", "budget_range": "$50–250k", "project_types": ["Riparian planting"], "themes": ["Salmon habitat"], "stage": "Ready to implement", "project_title": "Salmon Restoration", "description": "Restore riparian"}, 'selected_program': hctf.iloc[0].to_dict(), 'page': 'grant_readiness'})
                st.rerun()

st.markdown('<div class="hero"><p class="eyebrow">Funding Matcher</p><h1>EcoProject Navigator</h1><p style="color:var(--muted);margin-top:8px;">Match your project to BC environmental funding</p><div class="pill" style="margin-top:12px;"><span class="dot"></span>48+ programs · Smart matching · AI insights</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-header"><div class="section-number">1</div><div><h3>Who are you?</h3><p class="section-sub">Applicant type affects eligibility</p></div></div><div class="input-section">', unsafe_allow_html=True)
org_name = st.text_input("Organization", placeholder="e.g., Pacheedaht First Nation")
name = st.text_input("Your name", placeholder="e.g., Sarah Johnson")
email = st.text_input("Email", placeholder="e.g., sarah.johnson@example.com")
applicant_type = st.selectbox("Applicant type", ["First Nation", "Indigenous organization", "Municipality / Regional District", "Non-profit / Charity", "For-profit business", "University / Research institute", "Other"], index=None, placeholder="Select your organization type...")
partners = st.text_input("Partners (optional)", placeholder="e.g., Mosaic Forest Management, UBC Forestry")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-header"><div class="section-number">2</div><div><h3>Project basics</h3><p class="section-sub">💡 Tip: Mention specific funders (e.g., SFI, HCTF) for better matches</p></div></div><div class="input-section">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    region = st.text_input("Region / Watershed", placeholder="e.g., Barkley Sound, Cowichan River")
    budget_range = st.selectbox("Budget", ["<$50k", "$50–250k", "$250k–1M", ">1M"])
    stage = st.selectbox("Stage", ["Idea", "Planning", "Ready to implement", "Shovel-ready"])
with col2:
    project_types = st.multiselect("Project type(s)", ["Culvert replacement", "Road deactivation / upgrades", "Riparian planting", "Instream LWD / channel work", "Forest restoration", "Planning / assessment", "Monitoring", "Community engagement / education", "Land acquisition / conservation"], placeholder="Select project activities...")
    themes = st.multiselect("Themes", ["Climate adaptation", "Salmon habitat", "Watershed health", "Flood resilience", "Wildfire resilience", "Forest roads & access", "Erosion & sediment", "Water quality", "Biodiversity", "Wetlands & beavers", "Drinking water protection", "Community engagement / stewardship"], placeholder="Select focus areas...")
project_title = st.text_input("Project title", placeholder="e.g., Climate Smart Forestry Initiative")
description = st.text_area("Description", height=120, placeholder="Describe your project. Mention specific programs (SFI, HCTF, etc.) if known...")
st.markdown("</div><hr>", unsafe_allow_html=True)

def render_matches(df):
    st.markdown('<div class="section-header"><div class="section-number">3</div><div><h3>Your matches</h3><p class="section-sub">Sorted by fit score (keyword matches highlighted)</p></div></div>', unsafe_allow_html=True)
    submission_id = st.session_state.get("submission_id")
    for idx, row in df.iterrows():
        program_name = row.get("Program_Name", "Unknown")
        
        # Check if this was a keyword match
        user_text = f"{st.session_state.get('user_intake', {}).get('project_title', '')} {st.session_state.get('user_intake', {}).get('description', '')}".lower()
        is_keyword_match = check_keyword_match(user_text, program_name, row.get("Funder_Organization", "")) > 0
        
        st.markdown('<div class="program-card">', unsafe_allow_html=True)
        keyword_badge = '<span class="keyword-badge">🎯 KEYWORD MATCH</span>' if is_keyword_match else ''
        st.markdown(f'<div class="program-top"><div><p class="eyebrow">Funding opportunity</p><h3>🐟 {program_name}{keyword_badge}</h3></div><div class="score-badge"><span style="font-size:1.4rem;">{int(row["Score"])}</span><small style="margin-left:4px;">match</small></div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-grid"><div class="metric-card"><p class="metric-label">Max grant</p><p class="metric-value">{row.get("Max_Grant_Amount","—")}</p></div><div class="metric-card"><p class="metric-label">Deadline</p><p class="metric-value">{row.get("Application_Deadline","—")}</p></div><div class="metric-card"><p class="metric-label">Competition</p><p class="metric-value">{row.get("Competitiveness_Level","—")}</p></div></div>', unsafe_allow_html=True)
        if row.get("Program_Description"):
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.write(row["Program_Description"])
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💧 Request Deep Dive", key=f"dd_{idx}", use_container_width=True):
                if submission_id and trigger_deep_dive(submission_id, row.get("id"), program_name):
                    st.success("✅ Analysis requested!")
                    st.info(f'📧 **Email within 24 hours** to **{st.session_state["user_intake"].get("email")}**\n\nAnalyzing: **{program_name}**\n\n✓ GO/NO-GO score\n✓ Strategic actions\n✓ Fit analysis\n✓ Required documents\n✓ Budget guidance\n✓ Red flags')
                    st.markdown("""<script>
                    const style = document.createElement('style');
                    style.textContent = '@keyframes bubble{0%{bottom:-50px;opacity:1}100%{bottom:100vh;opacity:0}}.bubble{position:fixed;background:radial-gradient(circle,#5eead4,#14b8a6);border-radius:50%;animation:bubble 5s ease-in infinite;z-index:9999;pointer-events:none}';
                    document.head.appendChild(style);
                    for(let i=0;i<12;i++){
                        const b = document.createElement('div');
                        b.className = 'bubble';
                        const size = Math.random()*15+8;
                        b.style.width = b.style.height = size+'px';
                        b.style.left = Math.random()*100+'%';
                        b.style.animationDelay = Math.random()*2+'s';
                        b.style.animationDuration = (Math.random()*2+4)+'s';
                        document.body.appendChild(b);
                        setTimeout(()=>b.remove(), 6000);
                    }
                    </script>""", unsafe_allow_html=True)
                else:
                    st.warning("Fill form first" if not submission_id else "Failed")
        with c2:
            if has_template(program_name):
                if st.button("📋 Grant Readiness", key=f"gr_{idx}", type="primary", use_container_width=True):
                    st.session_state.update({'selected_program': row.to_dict(), 'page': 'grant_readiness'})
                    st.rerun()
            else:
                st.button("📋 Grant Readiness", key=f"gr_{idx}", disabled=True, help="Soon", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.success(f"✅ {len(df)} programs matched!")

if st.button("🔍 Find funding matches", type="primary", use_container_width=True):
    if not applicant_type:
        st.error("⚠️ Please select applicant type")
        st.stop()
    if not email or not name:
        st.error("⚠️ Please enter your name and email")
        st.stop()
    
    st.session_state['user_intake'] = {"organization": org_name, "name": name, "email": email, "applicant_type": applicant_type, "region": region, "budget_range": budget_range, "project_types": project_types, "themes": themes, "stage": stage, "project_title": project_title, "description": description, "partners": partners}
    
    submission_fields = {
        "Organization": org_name if org_name else f"{applicant_type} Organization",
        "Name": name,
        "Email": email,
        "Applicant Type": applicant_type,
        "Region": region if region else "BC",
        "Budget Range": budget_range,
        "Project Types": ", ".join(project_types) if project_types else "",
        "Project Title": project_title if project_title else "Untitled Project",
        "Description": description if description else "",
        "Stage": stage,
        "Themes": ", ".join(themes) if themes else "",
        "Partners": partners if partners else "",
    }
    
    submission_id = create_project_submission(submission_fields)
    if submission_id:
        st.session_state['submission_id'] = submission_id
        st.success(f"✅ Saved! ({name} | {email})")
    else:
        st.stop()
    
    df = load_funding_programs()
    if df.empty:
        st.warning("No programs")
        st.stop()
    
    # Enhanced scoring with new parameters
    df["RawScore"] = df.apply(
        lambda r: raw_score_program(
            r, applicant_type, project_types, themes, budget_range, 
            region, stage, project_title, description, partners
        ), 
        axis=1
    )
    df["Score"] = df["RawScore"].round().astype(int)
    df = df.sort_values(by=["Score", "Program_Name"], ascending=[False, True])
    
    if not df.empty and submission_id:
        update_project_submission(submission_id, {"Top Program ID": df.iloc[0]["id"]})
    
    st.session_state['matches'] = df
    st.balloons()  # Celebrate finding matches!

if st.session_state.get("matches") is not None and not st.session_state["matches"].empty:
    render_matches(st.session_state["matches"])
