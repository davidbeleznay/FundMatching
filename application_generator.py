"""
Application Example Generator
Creates complete mock applications based on user responses to readiness questions
"""

from datetime import datetime
from typing import Dict


def generate_sfi_application(user_intake: Dict, responses: Dict, program: Dict) -> str:
    """
    Generate a complete SFI Climate Smart Forestry application example
    
    Args:
        user_intake: Original project intake data
        responses: User's answers to readiness questions  
        program: Selected program details
        
    Returns:
        Formatted application text ready for download
    """
    
    # Extract data
    org_name = user_intake.get('organization', '[Organization Name]')
    project_title = user_intake.get('project_title', '[Project Title]')
    region = user_intake.get('region', '[Region]')
    budget_range = user_intake.get('budget_range', '[Budget]')
    description = user_intake.get('description', '[Project Description]')
    
    # Get responses with fallbacks
    org_eligibility = responses.get('org_eligibility', '[Describe your governance structure and forest management authority]')
    forest_classification = responses.get('forest_classification', '[Provide forest classification and age class]')
    scalability = responses.get('scalability', '[Explain how this methodology can be scaled or replicated]')
    cultural_benefits = responses.get('cultural_benefits', '[List specific cultural and socioeconomic benefits]')
    climate_benefits = responses.get('climate_benefits', '[Describe measurable climate benefits]')
    team_expertise = responses.get('team_expertise', '[List key team members and their experience]')
    carbon_quantification = responses.get('carbon_quantification', '[Describe carbon quantification methodology if applicable]')
    project_duration = responses.get('project_duration', '[Specify 1-year or 2-year project with milestones]')
    budget_justification = responses.get('budget_justification', '[Provide budget breakdown]')
    
    # Generate application
    application = f"""
SFI INDIGENOUS-LED CLIMATE SMART FORESTRY
APPLICATION EXAMPLE

Generated: {datetime.now().strftime('%B %d, %Y')}
Note: This is a template based on your responses. Review and customize before submitting.

═══════════════════════════════════════════════════════════════
COVER PAGE
═══════════════════════════════════════════════════════════════

PROJECT TITLE
{project_title}

PROJECT SUMMARY
{description}

PRIMARY CONTACT
Name: {user_intake.get('name', '[Your Name]')}
Organization: {org_name}
Email: {user_intake.get('email', '[Your Email]')}
Phone: [Your Phone Number]

ORGANIZATION DESCRIPTION & ELIGIBILITY
{org_eligibility}

═══════════════════════════════════════════════════════════════
PROJECT NARRATIVE
═══════════════════════════════════════════════════════════════

1. PROJECT DURATION & TIMELINE
{project_duration}

2. PROJECT LOCATION
Region: {region}
Geographic Area: [Provide specific geographic coordinates or description]
Forest Tenure: [Describe your forest tenure arrangement]

3. FOREST CLASSIFICATION & AGE CLASS
{forest_classification}

4. PROJECT ACTIVITIES & CLIMATE SMART FORESTRY PRACTICES

Overview:
{description}

Specific Activities:
{_format_project_types(user_intake.get('project_types', []))}

Alignment with Climate Smart Forestry:
This project implements climate smart forestry practices that will:
- Reduce greenhouse gas emissions from forestry operations
- Enhance forest resilience to climate change impacts
- Support long-term forest health and productivity
- Integrate traditional knowledge with modern forestry science

5. METHODS & METHODOLOGIES

Implementation Approach:
[Describe your specific methods for each activity - e.g., site selection criteria, 
planting techniques, monitoring protocols, community engagement processes]

Technical Standards:
[Reference any technical standards or best practices you'll follow - e.g., BC silviculture 
guidelines, traditional ecological knowledge protocols, industry standards]

Quality Assurance:
[Describe how you'll ensure quality of work - e.g., RPF oversight, elder review, 
field inspections, photo documentation]

6. EXPECTED OUTCOMES

For Forests:
{climate_benefits}

Scalability & Applicability:
{scalability}

For Community:
{cultural_benefits}

Measurable Outcomes:
[Provide specific, measurable outcomes - e.g.:
• Hectares restored: [XX ha]
• Trees planted: [XX,XXX]
• Carbon stored/emissions avoided: [XX tonnes CO2e] (if quantifiable)
• Jobs created: [XX positions]
• Training opportunities: [XX community members]
• Traditional use sites protected: [XX sites]]

7. CARBON & GHG BENEFITS

{carbon_quantification if carbon_quantification else "While we are not providing detailed carbon quantification at this stage, our project will contribute to climate benefits through [describe general mechanisms - e.g., increased carbon storage in standing forests, avoided emissions from reduced slash burning, enhanced resilience reducing risk of carbon loss from disturbance]."}

8. SOCIOECONOMIC & CULTURAL BENEFITS

{cultural_benefits}

Economic Benefits:
• Employment: [Describe jobs created - number, duration, skill development]
• Revenue: [Describe any revenue opportunities - timber, non-timber products, eco-tourism]
• Capacity Building: [Describe training and skill development opportunities]

Cultural Benefits:
• Traditional Knowledge: [Describe how TK is integrated and strengthened]
• Cultural Sites: [Describe protection/enhancement of culturally significant areas]
• Intergenerational Learning: [Describe elder involvement and youth engagement]
• Cultural Practices: [Describe support for traditional harvesting, ceremonies, etc.]

9. SCALABILITY & BROADER APPLICABILITY

{scalability}

Regional Application:
[Describe how other First Nations in your region could adopt this approach]

National Relevance:
[Describe how the methodology could be adapted to other forest types/regions across Canada]

Knowledge Sharing:
[Describe your commitment to sharing lessons learned - e.g., presentations at 
SILVA21, case studies, workshops with neighboring Nations]

═══════════════════════════════════════════════════════════════
PROJECT TEAM & CAPACITY
═══════════════════════════════════════════════════════════════

KEY TEAM MEMBERS

{team_expertise}

Organizational Capacity:
[Describe your organization's track record with similar projects, forestry operations, 
grant management, community engagement, etc.]

Partnership & Collaboration:
{_format_partnerships(user_intake.get('partners', ''))}

Commitment to Knowledge Keepers & Experts:
We are committed to working collaboratively with:
• Community elders and knowledge holders
• Registered Professional Foresters
• SFI technical advisors
• [Other relevant partners - e.g., university researchers, conservation organizations]

═══════════════════════════════════════════════════════════════
DETAILED BUDGET & COST-EFFECTIVENESS
═══════════════════════════════════════════════════════════════

BUDGET SUMMARY
Total Project Budget: {_estimate_budget_amount(budget_range)}
SFI Funding Requested: {_estimate_budget_amount(budget_range)}
Matching/In-Kind Contributions: [Specify amount and source]

DETAILED BUDGET BREAKDOWN

{budget_justification}

Note: The budget follows SFI guidelines with:
• Implementation costs (field activities, equipment): [XX%] 
• Project management & staffing: [XX%] (less than 40%)
• Community engagement & training: [XX%]
• Administrative costs: [XX%] (less than 10%)

MAJOR MILESTONES & DELIVERABLES

{_generate_milestones(project_duration)}

COST-EFFECTIVENESS
[Explain why this represents good value - e.g., cost per hectare treated, leverage of 
in-kind contributions, long-term benefits beyond project period, replicability reducing 
future costs for others]

═══════════════════════════════════════════════════════════════
MEASUREMENT, MONITORING & REPORTING
═══════════════════════════════════════════════════════════════

MONITORING PLAN

Baseline Data:
[Describe baseline measurements you'll take before project implementation]

Ongoing Monitoring:
[Describe how you'll track progress during implementation - e.g., site visits, 
photo points, data collection protocols]

Success Indicators:
[List specific, measurable indicators - e.g.:
• Survival rates of planted trees (target: >80% after year 1)
• Forest structure diversity indices
• Community participation rates
• Traditional use site access maintained
• Carbon storage estimates (if applicable)]

REPORTING COMMITMENT

We commit to providing:
• Interim progress reports as required by SFI
• Final comprehensive report with:
  - Activities completed
  - Outcomes achieved vs. targets
  - Lessons learned
  - Photos and documentation
  - Financial reporting
  
• Collaborative engagement with SFI team throughout project

KNOWLEDGE SHARING

We will share our results through:
[Describe your knowledge sharing plans - e.g., presentations at conferences, 
case studies, workshops, social media, community reports]

═══════════════════════════════════════════════════════════════
SUPPORTING DOCUMENTS (TO BE ATTACHED)
═══════════════════════════════════════════════════════════════

Required:
☐ Band Council Resolution supporting the project
☐ Letter from Chief & Council
☐ Proof of forest management authority (e.g., Community Forest Agreement)
☐ Detailed budget spreadsheet with timeline
☐ Map of project area
☐ Letters of support from partners (if applicable)

Recommended (Strengthens Application):
☐ Photos of current site conditions
☐ Technical reports or assessments
☐ Previous project success examples
☐ Community consultation documentation
☐ Carbon quantification methodology details
☐ Forest management plan excerpts

═══════════════════════════════════════════════════════════════
DECLARATION
═══════════════════════════════════════════════════════════════

On behalf of {org_name}, I declare that:

• The information provided in this application is accurate and complete
• We have the authority to manage the forests described in this proposal
• We commit to implementing this project in accordance with SFI standards
• We will provide required reporting and engage collaboratively with SFI
• Project funds will be expended by March 31, 2027
• We understand that SFI may request clarification or revision of this proposal

Signature: _______________________________  Date: _________________

Name: {user_intake.get('name', '[Your Name]')}
Title: [Your Title]

═══════════════════════════════════════════════════════════════
END OF APPLICATION EXAMPLE
═══════════════════════════════════════════════════════════════

NEXT STEPS:
1. Review this application carefully and fill in any [bracketed] sections
2. Gather all required supporting documents listed above
3. Have your RPF review technical sections
4. Get approval from Chief & Council
5. Submit to: Rachel.Hamilton@forests.org

Questions? Contact SFI:
- Rachel Hamilton: Rachel.Hamilton@forests.org
- Jeffrey Ross: Jeffrey.Ross@forests.org
- Lauren Cooper: Lauren.Cooper@forests.org
"""
    
    return application


def _format_project_types(project_types: list) -> str:
    """Format project types as bullet list"""
    if not project_types:
        return "• [List your specific project activities]"
    return "\\n".join(f"• {pt}" for pt in project_types)


def _format_partnerships(partners: str) -> str:
    """Format partnerships section"""
    if not partners or partners.strip() == "":
        return "[Describe any partnerships - e.g., with forest companies, universities, conservation organizations, neighboring First Nations]"
    return f"We are partnering with: {partners}\\n\\n[Provide details on each partner's role and contribution to the project]"


def _estimate_budget_amount(budget_range: str) -> str:
    """Convert budget range to specific amount for example"""
    mapping = {
        "<$50k": "$45,000",
        "$50–250k": "$180,000",
        "$250k–1M": "$300,000",
        ">1M": "$300,000 (SFI maximum)"
    }
    return mapping.get(budget_range, "[Budget Amount]")


def _generate_milestones(project_duration: str) -> str:
    """Generate milestone examples based on project duration"""
    if "2-year" in project_duration or "2 year" in project_duration:
        return """
Year 1:
• Month 1-2: Finalize project planning, hire staff, procure equipment
• Month 3-4: Complete baseline assessments and site preparations
• Month 5-8: Implement Phase 1 field activities
• Month 9-10: Interim monitoring and data collection
• Month 11-12: Year 1 reporting to SFI

Year 2:
• Month 13-14: Review Year 1 lessons, adjust approach if needed
• Month 15-18: Implement Phase 2 field activities  
• Month 19-20: Complete final monitoring and assessments
• Month 21-22: Knowledge sharing activities (workshops, presentations)
• Month 23-24: Final reporting and project close-out
"""
    else:
        return """
• Month 1-2: Finalize project planning, hire staff, procure equipment
• Month 3-4: Complete site preparations and baseline data
• Month 5-8: Implement main field activities
• Month 9-10: Monitoring and assessment
• Month 11-12: Final reporting and knowledge sharing
"""
