"""
Document Template Generators
Creates example BCRs, letters of support, and other required documents

Last updated: 2025-12-18 - STREAMLIT CLOUD DEPLOYMENT FIX
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

THEREFORE BE IT RESOLVED THAT:

1. The Chief and Council of {org_name} authorize [PROJECT LEAD NAME & TITLE] 
   to submit a funding application to {program_name} on behalf of the Nation;

2. The Chief and Council support the implementation of {project_title} as 
   described in the attached project proposal;

3. [PROJECT LEAD NAME] is authorized to sign all necessary agreements, reports, 
   and documents related to this funding application and project implementation, 
   subject to final Chief and Council approval of any funding agreement;

4. This resolution remains in effect until the project is completed or until 
   rescinded by a subsequent Band Council Resolution.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MOVED BY:        [Councillor Name]
SECONDED BY:     [Councillor Name]

VOTE:
In Favour:       [  ]
Opposed:         [  ]
Abstained:       [  ]

RESULT:          CARRIED / DEFEATED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CERTIFIED TRUE COPY:

_____________________________     Date: _________________
Chief [Name]

_____________________________     Date: _________________
Band Administrator

HOW TO USE THIS TEMPLATE:
1. Fill in all [BRACKETED] sections
2. Present at Chief & Council meeting for approval
3. Get signatures from Chief and Administrator
4. Timeline: 2-4 weeks typically
"""
    
    return bcr


def generate_chief_letter_template(user_intake: Dict, program_name: str) -> str:
    """Generate a letter of support from Chief & Council template"""
    
    org_name = user_intake.get('organization', '[Your First Nation Name]')
    project_title = user_intake.get('project_title', '[Project Title]')
    
    letter = f"""
[First Nation Letterhead]

{datetime.now().strftime('%B %d, %Y')}

{program_name}
[Funder Contact]

Dear Selection Committee,

RE: Letter of Support for {project_title}

On behalf of the {org_name}, I am writing to express our strong support for 
the attached funding application.

[Customize with your project details and Nation's priorities]

Sincerely,

_____________________________
Chief [Name]
{org_name}
"""
    
    return letter


def generate_budget_template() -> str:
    """Generate a budget guide"""
    
    return """
BUDGET TEMPLATE GUIDE

A. IMPLEMENTATION COSTS (60-70%)
   - Site preparation
   - Materials & supplies
   - Equipment rental
   - Technical services

B. PROJECT MANAGEMENT (25%)
   - Staff salaries
   - Training

C. COMMUNITY ENGAGEMENT (7%)
   - Elder honoraria
   - Workshops

D. TRAVEL (3%)
   - Site visits
   - Meetings

E. ADMINISTRATIVE (Max 10%)
   - Financial admin
   - Insurance
"""


def generate_partnership_letter_template(user_intake: Dict, partner_name: str = "[Partner]") -> str:
    """Generate partnership letter template"""
    
    org_name = user_intake.get('organization', '[Organization]')
    project_title = user_intake.get('project_title', '[Project]')
    
    return f"""
[Partner Letterhead]

{datetime.now().strftime('%B %d, %Y')}

RE: Letter of Support for {org_name} - {project_title}

{partner_name} is pleased to support this application.

[Describe partnership and support being provided]

Sincerely,

_____________________________
[Name, Title]
{partner_name}
"""


def get_bcr_explainer() -> str:
    """Return BCR explainer"""
    return """
**What is a BCR?**

A Band Council Resolution is an official decision by Chief and Council that 
authorizes actions on behalf of the First Nation.

**Timeline:** 2-4 weeks typically
**Required for:** Nearly all First Nation grant applications
"""


def get_example_responses_by_question() -> Dict[str, Dict]:
    """Return example responses for questions"""
    
    return {
        "org_eligibility": {
            "weak": "We are a First Nation.",
            "strong": "We are a First Nation with a 20-year Community Forest Agreement covering 12,500 hectares.",
            "why_strong": "Specific and detailed"
        }
    }


def get_response_strengthening_tips(question_id: str, user_response: str) -> str:
    """Provide tips to strengthen responses"""
    
    if not user_response or len(user_response.split()) < 10:
        return "💡 Add more detail - aim for 3-5 sentences"
    
    return ""
