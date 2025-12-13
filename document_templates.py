"""
Document Template Generators
Creates example BCRs, letters of support, and other required documents
"""

from datetime import datetime
from typing import Dict


def generate_bcr_template(user_intake: Dict, program_name: str, project_title: str) -> str:
    """
    Generate a Band Council Resolution template
    
    Args:
        user_intake: User's project data
        program_name: Name of funding program
        project_title: Project title
        
    Returns:
        Formatted BCR text ready to customize
    """
    
    org_name = user_intake.get('organization', '[Your First Nation Name]')
    description = user_intake.get('description', '[Brief project description]')
    budget = user_intake.get('budget_range', '[Budget amount]')
    
    bcr = f"""
BAND COUNCIL RESOLUTION
{org_name}

Resolution Number: BCR-[YYYY-###]
Date: [Meeting Date]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT IS A BAND COUNCIL RESOLUTION (BCR)?
A BCR is an official decision made by Chief and Council that authorizes specific 
actions on behalf of the First Nation. For grant applications, the BCR demonstrates 
that leadership has reviewed and approved the project and authorized someone to 
submit the application.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RE: Authorization to Apply for {program_name} Funding

WHEREAS the {org_name} is committed to sustainable forest management, 
environmental stewardship, and climate action in our traditional territory;

WHEREAS an opportunity exists to apply for funding through the {program_name} 
to support the implementation of {project_title};

WHEREAS this project will provide the following benefits to our community:
    • {description}
    • Support climate adaptation and forest resilience
    • Create employment and training opportunities for community members
    • Enhance protection of cultural resources and traditional values
    • Strengthen our Nation's capacity for forest management;

WHEREAS the total project budget is estimated at {budget}, with up to 
[$ AMOUNT] requested from {program_name};

WHEREAS this project aligns with our Nation's strategic priorities for 
[environmental stewardship / economic development / cultural protection / 
climate action - SELECT RELEVANT];

THEREFORE BE IT RESOLVED THAT:

1. The Chief and Council of {org_name} authorize [PROJECT LEAD NAME & TITLE] 
   to submit a funding application to {program_name} on behalf of the Nation;

2. The Chief and Council support the implementation of {project_title} as 
   described in the attached project proposal;

3. [PROJECT LEAD NAME] is authorized to sign all necessary agreements, reports, 
   and documents related to this funding application and project implementation, 
   subject to final Chief and Council approval of any funding agreement;

4. The Lands Department [OR RELEVANT DEPARTMENT] is directed to provide 
   necessary support and resources for project development and implementation; and

5. This resolution remains in effect until the project is completed or until 
   rescinded by a subsequent Band Council Resolution.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MOVED BY:        [Councillor Name]
SECONDED BY:     [Councillor Name]

VOTE:
In Favour:       [  ] (Unanimous / List names)
Opposed:         [  ] (None / List names)
Abstained:       [  ] (None / List names)

RESULT:          CARRIED / DEFEATED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CERTIFIED TRUE COPY:

_____________________________     Date: _________________
Chief [Name]


_____________________________     Date: _________________
Band Administrator / Corporate Secretary


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW TO USE THIS TEMPLATE:

1. Fill in all [BRACKETED] sections
2. Customize the WHEREAS clauses to reflect your Nation's priorities
3. Insert the correct project lead name and title
4. Have your Band Administrator review for proper format
5. Present at Chief & Council meeting for approval
6. Get signatures from Chief and Administrator
7. Keep original for your records, provide copy to funder

TIMELINE:
• Draft BCR: 1-2 hours
• Schedule C&C meeting: 2-4 weeks (depends on meeting schedule)
• Approval & signatures: Same day as meeting
• Total time: 2-4 weeks typically

TIPS:
• Schedule early - some Nations only meet monthly
• Send draft to councillors in advance for review
• Be ready to answer questions at the meeting
• Have project details ready to present
"""
    
    return bcr


def generate_chief_letter_template(user_intake: Dict, program_name: str) -> str:
    """Generate a letter of support from Chief & Council template"""
    
    org_name = user_intake.get('organization', '[Your First Nation Name]')
    project_title = user_intake.get('project_title', '[Project Title]')
    
    letter = f"""
[First Nation Letterhead]
[Address]
[Phone] | [Email] | [Website]

{datetime.now().strftime('%B %d, %Y')}

Sustainable Forestry Initiative
Climate Smart Forestry Program
Rachel Hamilton, Manager, Conservation Programs
Rachel.Hamilton@forests.org

Dear Ms. Hamilton and SFI Selection Committee,

RE: Letter of Support for {project_title}

On behalf of the {org_name}, I am writing to express our strong support for 
the attached funding application to the SFI Indigenous-Led Climate Smart Forestry 
program.

[PARAGRAPH 1 - WHY THIS PROJECT MATTERS TO YOUR NATION]
Example: "Our traditional territory has been significantly impacted by [historical 
logging practices / climate change / forest health challenges]. This project represents 
a critical opportunity to [restore cultural values / implement traditional knowledge / 
build climate resilience] in our forests while creating meaningful benefits for our 
community members."

[PARAGRAPH 2 - ALIGNMENT WITH NATION'S PRIORITIES]
Example: "This project aligns directly with our Nation's strategic plan priorities 
for [environmental stewardship / economic development / cultural preservation / 
climate action]. Our Chief and Council have identified forest restoration and climate 
adaptation as key areas for investment, and this project will advance both goals while 
providing employment and training opportunities for our members."

[PARAGRAPH 3 - CAPACITY AND COMMITMENT]
Example: "Our Lands Department has successfully managed [NUMBER] environmental projects 
totaling $[AMOUNT] over the past [X] years, demonstrating our capacity to deliver 
results. We are committed to working collaboratively with SFI throughout this project 
and to sharing our learnings with other Indigenous communities across Canada."

[PARAGRAPH 4 - SUPPORT STATEMENT]
Example: "Our Chief and Council have reviewed this proposal and passed Band Council 
Resolution [BCR-YYYY-###] on [DATE] authorizing this application and expressing our 
full support for project implementation. We are committed to providing the necessary 
resources, staff time, and community engagement to ensure project success."

We respectfully request your favourable consideration of this application and look 
forward to partnering with SFI to advance climate smart forestry in our territory.

Sincerely,

_____________________________
Chief [Name]
{org_name}

cc: Chief and Council
    [Project Lead Name], Project Lead
    Nation's files

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW TO USE THIS TEMPLATE:

1. Use your Nation's official letterhead
2. Customize each paragraph in [BRACKETS] with specific details
3. Reference your actual BCR number and date
4. Have Chief review and sign
5. Include with your application

LENGTH: Keep to 1 page (single-sided)
FORMAT: Business letter format on letterhead
TONE: Professional but can include cultural context
"""
    
    return letter


def generate_budget_template() -> str:
    """Generate a budget spreadsheet template explanation"""
    
    budget_guide = """
SFI CLIMATE SMART FORESTRY - BUDGET TEMPLATE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BUDGET GUIDELINES (SFI Requirements):

✓ Implementation costs should be 60%+ of total
✓ Administrative costs MAX 10% of total
✓ Staff/travel/training should be <40% unless justified
✓ Rental expenses <10% unless justified
✓ Include milestones tied to deliverables

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECOMMENDED STRUCTURE:

YEAR 1 BUDGET (Example for $150,000 request)

A. IMPLEMENTATION COSTS (60-70%)                      $95,000
   ├─ Site Preparation                                $25,000
   │  • Manual brushing (50 ha @ $500/ha)             $25,000
   │
   ├─ Planting & Materials                            $45,000
   │  • Cedar seedlings (30,000 @ $1.20 each)         $36,000
   │  • Planting labor (contractor quote)             $9,000
   │
   ├─ Equipment & Supplies                            $15,000
   │  • ATV rental (6 months @ $1,200/mo)            $7,200
   │  • Tools and safety equipment                    $4,800
   │  • Field supplies                                $3,000
   │
   └─ Technical Services                              $10,000
      • RPF services (site assessment, prescriptions) $8,000
      • Survey/GPS work                               $2,000

B. PROJECT MANAGEMENT & STAFF (25%)                   $37,500
   ├─ Project Coordinator (0.5 FTE, 12 months)       $30,000
   ├─ Field Technician (seasonal, 6 months)          $7,500
   │
   └─ Training & Development                          $0
      • RPF mentorship for staff (in-kind)           

C. COMMUNITY ENGAGEMENT (7%)                          $10,500
   ├─ Elder honoraria (6 sessions @ $500)            $3,000
   ├─ Community workshops (3 events)                  $4,500
   ├─ Youth engagement activities                     $3,000

D. TRAVEL & MEETINGS (3%)                             $4,500
   ├─ Site visits & field travel                     $3,000
   ├─ Meetings with partners                         $1,500

E. ADMINISTRATIVE COSTS (4.5%)                        $6,750
   ├─ Financial administration                        $3,000
   ├─ Insurance                                       $2,000
   ├─ Office supplies & communications                $1,750

F. CONTINGENCY (Reserve, 0%)                          $0
   
YEAR 1 TOTAL:                                        $154,250
SFI REQUEST:                                         $150,000
IN-KIND CONTRIBUTION:                                $4,250

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MILESTONES & DELIVERABLES:

Milestone 1 (Month 3): Planning & Procurement Complete
• Deliverable: Site assessment report, procurement complete
• Budget: $15,000

Milestone 2 (Month 6): Site Preparation Complete  
• Deliverable: 50 ha brushed and ready for planting
• Budget: $35,000

Milestone 3 (Month 9): Planting Phase 1 Complete
• Deliverable: 30,000 cedar planted, survival monitoring begun
• Budget: $65,000

Milestone 4 (Month 12): Year 1 Reporting & Monitoring
• Deliverable: Interim report, monitoring data, financial report
• Budget: $35,000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IN-KIND & MATCHING CONTRIBUTIONS:

Cash Match:
• [Funder name]: $[Amount]
• Own-source revenue: $[Amount]

In-Kind:
• Community volunteer hours: [XX hours @ $25/hr = $XX,XXX]
• Equipment use (from partner): $[Amount]
• RPF technical services (donated): $[Amount]
• Elder knowledge sharing: [XX hours @ $50/hr = $XX,XXX]

TOTAL PROJECT VALUE: $[SFI Request + Match + In-kind]
LEVERAGE RATIO: [Total Project Value / SFI Request]

Example: $200,000 total / $150,000 SFI = 1.33:1 leverage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIPS FOR STRONG BUDGETS:

✓ Get actual quotes from contractors (not just estimates)
✓ Show unit costs ($/ha, $/tree, $/hour)
✓ Tie budget items to specific deliverables
✓ Justify any items over 10% of category
✓ Show in-kind contributions (demonstrates community investment)
✓ Include detailed line items (not just broad categories)
✓ Consider 2-year timeline if needed

❌ AVOID:
✗ Heavy equipment purchases (not eligible)
✗ Building/land purchases (not eligible)
✗ Admin costs >10%
✗ Vague categories without detail
✗ Salaries without justification
"""
    
    return budget_guide


def generate_partnership_letter_template(user_intake: Dict, partner_name: str = "[Partner Organization]") -> str:
    """Generate partnership letter of support template"""
    
    project_title = user_intake.get('project_title', '[Project Title]')
    org_name = user_intake.get('organization', '[First Nation Name]')
    
    letter = f"""
[Partner Organization Letterhead]

{datetime.now().strftime('%B %d, %Y')}

Sustainable Forestry Initiative
Rachel Hamilton, Manager, Conservation Programs
Rachel.Hamilton@forests.org

Dear Ms. Hamilton,

RE: Letter of Support for {org_name} - {project_title}

{partner_name} is pleased to provide this letter of support for {org_name}'s 
application to the SFI Indigenous-Led Climate Smart Forestry program.

[PARAGRAPH 1 - DESCRIBE PARTNERSHIP]
Example: "We have worked with {org_name} since [YEAR] on [forest management / 
restoration projects / technical planning]. Our organizations share a commitment 
to sustainable forestry practices and Indigenous-led stewardship."

[PARAGRAPH 2 - SPECIFIC SUPPORT WE'RE PROVIDING]
Example: "For this project, {partner_name} commits to providing:
• Technical support from our Registered Professional Foresters
• Equipment rental at cost (estimated $8,000 in-kind value)
• Training and mentorship for {org_name} staff
• Access to our carbon modeling tools and expertise
• Site visits and field consultation as needed"

[PARAGRAPH 3 - WHY THIS PROJECT MATTERS]
Example: "This project represents an important advancement in climate-smart forestry 
practices on Vancouver Island. The retention harvest and cedar enhancement approaches 
being piloted have significant potential for replication across coastal BC forests. 
We believe this work will contribute valuable knowledge to the broader forest management 
community."

[PARAGRAPH 4 - CONFIDENCE STATEMENT]
Example: "Based on our experience working with {org_name}, we are confident in their 
capacity to successfully deliver this project. Their team has demonstrated [strong 
technical skills / effective community engagement / successful project management] on 
previous initiatives."

We strongly encourage SFI to support this application.

Sincerely,

_____________________________
[Name, Title]
{partner_name}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHO CAN WRITE PARTNERSHIP LETTERS?

Strong partners to ask:
✓ Forest companies you work with (Mosaic, Western, etc.)
✓ Universities (UBC Forestry, UNBC, etc.)
✓ RPF consultants providing technical services
✓ Conservation organizations (SILVA21, etc.)
✓ Neighboring First Nations (if joint work)
✓ Provincial agencies (if collaborative relationship)

TIPS:
• Be specific about what they're contributing
• Quantify in-kind contributions ($$ value)
• Have partner on letterhead, signed
• Get letters BEFORE submitting (not "will obtain")
• Letters should be max 1 page
"""
    
    return letter


def get_bcr_explainer() -> str:
    """Return a simple BCR explainer for help text"""
    return """
**What is a BCR?**

A Band Council Resolution (BCR) is an official decision by Chief and Council 
that authorizes actions on behalf of the First Nation. For grants, it shows:
• Leadership has reviewed and approved the project
• Someone is authorized to submit the application and sign agreements
• The project aligns with Nation's priorities

**Timeline:** Usually 2-4 weeks (depends on meeting schedule)

**Required for:** Nearly all First Nation grant applications

[Click to download BCR template]
"""


def get_example_responses_by_question() -> Dict[str, Dict]:
    """
    Return example responses for each question to help users strengthen their answers
    Based on successful SFI applications
    """
    
    return {
        "org_eligibility": {
            "weak": "We are a First Nation with a Community Forest.",
            "strong": "We are Pacheedaht First Nation with a 20-year Community Forest Agreement covering 12,500 hectares in the Sarita and Carmanah watersheds. Our Lands Department, operating under delegation from Chief and Council, has full authority over forest management planning, harvesting decisions, and restoration activities within our CFA. We have been actively managing these forests since 2015 with a focus on ecosystem-based management and cultural values integration.",
            "why_strong": "Specific geography, clear authority structure, demonstrates experience, shows values alignment"
        },
        
        "forest_classification": {
            "weak": "Old growth and second growth forest.",
            "strong": "Coastal Western Hemlock (CWH) biogeoclimatic zone, primarily vh1 and vm1 site series. Forest stands are predominantly 60-100 year old second growth western hemlock and Douglas-fir with scattered legacy western redcedar (150-300 years old). Site index ranges from SI 25-35. Stand densities average 800-1200 stems/ha with basal areas of 45-65 m²/ha.",
            "why_strong": "Uses technical forestry terminology, provides specific data, shows professional knowledge"
        },
        
        "scalability": {
            "weak": "Other First Nations could do something similar.",
            "strong": "Our approach combines traditional ecological knowledge with modern LiDAR analysis to identify priority cedar restoration sites - a methodology that can be applied by any coastal First Nation with forest tenure and access to provincial LiDAR data (freely available). The retention harvest prescriptions we're developing are designed as a modular framework that can be adapted across different biogeoclimatic zones, site series, and stand conditions. We estimate this approach could be scaled to 50,000+ hectares across neighboring Nuu-chah-nulth territories and have committed to sharing our protocols through the BC First Nations Forestry Council and SILVA21 network. Cost-effectiveness improves at scale as methodology development costs are one-time while application costs are linear.",
            "why_strong": "Specific mechanism for transfer, quantifies scale potential, names actual replication opportunities, addresses economics"
        },
        
        "cultural_benefits": {
            "weak": "Will help preserve our culture and create some jobs.",
            "strong": "• Enhanced access to traditional medicines: Restoration of understory diversity will support devil's club, salal, and huckleberry harvesting at 8 culturally significant sites\n• Employment & training: Minimum 3 full-time positions (6 months each) for community members, plus youth forestry training program reaching 12 participants\n• Protection of cultural heritage: Retention harvest approach will protect 15 identified culturally modified trees and 4 ceremonial bark-harvesting sites\n• Intergenerational knowledge transmission: Elder-led field sessions (6 planned) where traditional cedar knowledge is shared with youth participants\n• Food security: Restoration of traditional food species including crabapple and salal across 100+ hectares",
            "why_strong": "Specific and quantified, multiple benefit types, shows planning depth, connects to traditional practices"
        },
        
        "climate_benefits": {
            "weak": "Will reduce emissions and help with climate change.",
            "strong": "This project provides climate benefits through three mechanisms: (1) Emissions reduction - our retention harvest approach avoids slash burning of an estimated 500 tonnes of biomass, preventing release of approximately 250 tonnes CO2e compared to conventional clearcut; (2) Enhanced carbon storage - retaining 15-20% basal area maintains an additional 1,200 tonnes CO2 in live tree biomass over the 50-year period; (3) Climate adaptation - selection of drought-tolerant western redcedar provenances from 200m lower elevation increases seedling survival under projected +2°C warming scenarios, building forest resilience to more frequent drought stress.",
            "why_strong": "Three specific mechanisms, quantified where possible, shows technical understanding, connects to climate science"
        },
        
        "bcr_status": {
            "weak": "Will get one.",
            "strong": "BCR approved at Chief & Council meeting on November 30, 2024 (BCR-2024-087). Resolution authorizes Lands Manager Sarah Johnson to submit application and sign funding agreements subject to final C&C approval. Original BCR attached with application.",
            "why_strong": "Specific date, BCR number, named signatory, confirms availability"
        },
        
        "timeline_feasibility": {
            "weak": "Yes, we can do it in 2 years.",
            "strong": "Yes - realistic timeline: Application submission January 2025, anticipated approval March 2025, field activities begin May 2025 (optimal planting window). Year 1: Site prep May-June, planting June-July, monitoring August-October, interim report December. Year 2: Expansion planting May-July 2026, full season monitoring, final reporting Q1 2027. This timeline accounts for: seasonal planting windows (May-July optimal), Chief & Council meeting schedules (monthly), permit processing times (2-3 months), and buffer for weather delays. All expenditures will be completed by March 15, 2027, meeting SFI's March 31 deadline.",
            "why_strong": "Month-by-month detail, accounts for constraints, shows realistic planning, addresses the deadline explicitly"
        },
        
        "measurable_outcomes": {
            "weak": "Will restore some hectares and plant trees.",
            "strong": "• 500 hectares treated with retention harvest (targeting 15-20% basal area retention)\n• 30,000 western redcedar seedlings planted across 100 hectares\n• 15 culturally modified trees protected through harvest retention\n• 4 community members employed (total 18 person-months)\n• 12 youth trained in forestry practices (120 total training hours)\n• 8 traditional use sites enhanced for cultural access\n• 250 tonnes CO2e emissions avoided (vs. conventional clearcut with slash burning)\n• Baseline data established at 20 permanent monitoring plots",
            "why_strong": "Every outcome quantified, diverse benefit types, shows comprehensive planning"
        }
    }


def get_response_strengthening_tips(question_id: str, user_response: str) -> str:
    """
    Provide tips to strengthen a user's response based on common patterns
    
    Args:
        question_id: ID of the question
        user_response: User's current answer
        
    Returns:
        Tips for improvement
    """
    
    if not user_response or len(user_response.split()) < 10:
        return "💡 Add more detail - aim for 3-5 sentences with specific information"
    
    # Check for common patterns
    tips = []
    
    response_lower = user_response.lower()
    
    # Generic tips based on content
    if question_id == "cultural_benefits":
        if "job" in response_lower but "employment" not in response_lower:
            tips.append("Use 'employment' instead of 'jobs' for more professional tone")
        if not any(char.isdigit() for char in user_response):
            tips.append("Quantify benefits - how many positions? How many youth? How many sites?")
    
    if question_id == "climate_benefits":
        if "help" in response_lower or "good for" in response_lower:
            tips.append("Be specific about mechanism - HOW does it help climate?")
        if not any(word in response_lower for word in ["emissions", "carbon", "ghg", "co2", "storage", "sequestration"]):
            tips.append("Include climate terminology - emissions reduction, carbon storage, or adaptation")
    
    if question_id in ["measurable_outcomes", "budget_justification"]:
        if not any(char.isdigit() for char in user_response):
            tips.append("Add specific numbers - hectares, trees, people, dollars, tonnes")
    
    if tips:
        return "💡 **Strengthen this answer:**\n" + "\n".join(f"• {tip}" for tip in tips)
    
    return ""
