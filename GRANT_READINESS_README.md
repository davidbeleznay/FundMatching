# Funding Templates System - Grant Readiness Feature

## What We Built

A template-based question generation system that helps users prepare funding applications. When a user finds a matching funding program, they can click **"Grant Readiness"** to get:

1. **Smart Questions** - Personalized based on their project
2. **Application Checklist** - Documents and tasks they'll need
3. **Readiness Score** - How prepared they are to apply

## Architecture

```
FundMatching/
├── app.py                          # Main Streamlit app (updated with Grant Readiness button)
├── grant_readiness_page.py        # Grant Readiness UI
├── funding_templates/
│   ├── __init__.py
│   ├── template_engine.py          # Core template logic
│   ├── program_mapper.py           # Maps Airtable programs to templates
│   └── templates/
│       └── sfi-climate-smart-forestry.json  # First template (SFI)
```

## How It Works

### 1. User Flow

```
User submits intake form
    ↓
Sees matching programs with scores
    ↓
Clicks "Grant Readiness" button
    ↓
Gets personalized questions + checklist
    ↓
Answers questions
    ↓
Sees readiness score (0-100%)
```

### 2. Template System

Each funding program has a JSON template with:

**Questions:**
- `critical` - Must-haves for application
- `project_specific` - Based on user's project details
- `strengthen` - Optional but competitive advantages

**Checklist Items:**
- `critical` - Required before applying (BCR, letters, etc.)
- `project_specific` - Conditional based on project type
- `strengthen` - Optional items that improve chances

### 3. Smart Features

- **Conditional Logic**: Questions only show if relevant
  - Example: "How does this scale to 20,000+ ha?" only shows if project < 20,000 ha
  
- **Smart Defaults**: Region-specific hints
  - Example: Vancouver Island → "Likely CWH biogeoclimatic zone"
  
- **Personalization**: Questions adapted to user's project
  - Inserts project size, budget, location into questions

## Current Templates

✅ **SFI Indigenous-Led Climate Smart Forestry**
- 9 questions (3 critical, 4 project-specific, 2 strengthen)
- 10 checklist items
- Fully tested

🔜 **Coming Soon** (add more as needed):
- BC Salmon Restoration & Innovation Fund
- FWCP Watershed Programs
- Habitat Conservation Trust Foundation
- ECCC Nature Smart Climate Solutions

## Adding New Templates

### Step 1: Create Template JSON

Copy `funding_templates/templates/sfi-climate-smart-forestry.json` and modify:

```json
{
  "program_id": "your-program-id",
  "program_name": "Your Program Name",
  "questions": [
    {
      "id": "unique_question_id",
      "category": "critical|project_specific|strengthen",
      "question": "Your question text with {placeholders}",
      "why": "Why this is being asked",
      "required": true|false,
      "scoring_weight": 10
    }
  ],
  "checklist_items": {
    "critical": [...],
    "project_specific": [...],
    "strengthen": [...]
  }
}
```

### Step 2: Add Program Mapping

Edit `funding_templates/program_mapper.py`:

```python
PROGRAM_TEMPLATE_MAP = {
    "Your Program Name (from Airtable)": "your-program-id",
    ...
}
```

### Step 3: Test

1. Run your Streamlit app
2. Submit intake form with test data
3. Click "Grant Readiness" on your program
4. Verify questions show correctly

## Question Features

### Conditional Logic

Show questions only when relevant:

```json
{
  "conditional": {
    "field": "project_size",
    "operator": "<",
    "value": 20000
  }
}
```

Supported operators: `<`, `>`, `<=`, `>=`, `==`, `!=`, `contains`, `not_contains`, `in`, `not_in`

### Smart Defaults

Provide region-specific hints:

```json
{
  "smart_default": {
    "Vancouver Island": "Likely CWH (Coastal Western Hemlock) zone",
    "Interior": "Check if IDF, ICH, or SBS zone"
  }
}
```

### Examples

Help users with good answers:

```json
{
  "examples": [
    "Example answer 1",
    "Example answer 2"
  ]
}
```

## Checklist Features

### Conditional Items

Show checklist items based on project:

```json
{
  "item": "Forestry permits",
  "conditional": {
    "field": "project_types",
    "operator": "contains",
    "value": "forest"
  }
}
```

### Time Estimates

Help users plan:

```json
{
  "item": "Band Council Resolution",
  "time_estimate": "2-4 weeks",
  "priority": "HIGH"
}
```

## File Structure

### template_engine.py

Core classes:
- `FundingTemplate` - Single template with questions/checklist
- `TemplateManager` - Loads and manages multiple templates

Key methods:
- `get_questions(user_intake)` - Returns relevant questions
- `get_checklist(user_intake)` - Returns smart checklist
- `calculate_readiness_score(responses)` - Scores completion (0-100%)
- `estimate_time_to_ready(checklist, completed)` - Weeks remaining

### grant_readiness_page.py

UI components:
- `show_grant_readiness_page()` - Main page
- `show_question()` - Display single question
- `show_checklist_section()` - Display checklist
- `show_checklist_item()` - Single checklist item

## Two Button Flow

Each funding match now has **two buttons**:

### 🔍 Deep Dive (Existing)
- Triggers your Make.com automation
- Generates AI analysis report
- Uses Perplexity API

### 📋 Grant Readiness (New)
- Shows template-based questions
- Displays smart checklist
- Calculates readiness score
- **Only shows if template exists** for that program

## Next Steps

1. **Test with real data**: Try the SFI template with a First Nation project
2. **Add more templates**: Build 4-5 core programs you see often
3. **Refine questions**: Based on user feedback, improve question clarity
4. **Add features**: 
   - Save/export responses
   - Generate application drafts
   - Document templates (BCR, letters)

## Development Notes

- Templates stored as JSON for easy editing
- No AI needed - pure logic-based
- Fast (< 1 second to generate questions)
- Scalable (can handle hundreds of templates)
- User data stored in `st.session_state`

## Questions?

Template not working? Check:
1. Is program name in `program_mapper.py`?
2. Does JSON file exist in `templates/` folder?
3. Are question IDs unique?
4. Is conditional logic valid?

---

**Built:** December 13, 2024  
**Status:** Production-ready for first template (SFI)  
**Expansion:** Add templates as needed
