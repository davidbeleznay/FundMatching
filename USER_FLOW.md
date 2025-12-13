# Complete User Flow: Two-Button System

## User Journey

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: INTAKE FORM (2 minutes)                           │
│  • Organization details                                     │
│  • Project basics (region, budget, type, themes)           │
│  • Short description                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    Click "Find Matches"
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: MATCHED PROGRAMS (Ranked by Score)                │
│                                                             │
│  ╔═══════════════════════════════════════════════════════╗ │
│  ║ 🌊 SFI Indigenous-Led Climate Smart Forestry    [95] ║ │
│  ║ Min: $50K  Max: $300K  Deadline: Rolling              ║ │
│  ║                                                        ║ │
│  ║ Two Action Buttons:                                   ║ │
│  ║ ┌──────────────┐  ┌──────────────────────┐           ║ │
│  ║ │ 🔍 Deep Dive │  │ 📋 Grant Readiness   │           ║ │
│  ║ └──────────────┘  └──────────────────────┘           ║ │
│  ╚═══════════════════════════════════════════════════════╝ │
│                                                             │
│  [More programs below with same two-button layout...]      │
└─────────────────────────────────────────────────────────────┘
                    ↓                          ↓
          ┌─────────────────┐        ┌──────────────────────┐
          │  PATH A:        │        │  PATH B:             │
          │  DEEP DIVE      │        │  GRANT READINESS     │
          └─────────────────┘        └──────────────────────┘
                    ↓                          ↓
┌────────────────────────────┐    ┌──────────────────────────┐
│ DEEP DIVE (Existing)       │    │ GRANT READINESS (New)    │
│                            │    │                          │
│ • Triggers Make.com        │    │ • 9 Smart Questions      │
│ • Calls Perplexity API     │    │   - Critical (3)         │
│ • Analyzes funder criteria │    │   - Project-specific (4) │
│ • Strategic positioning    │    │   - Strengthen (2)       │
│ • Red flags to avoid       │    │                          │
│ • Generates AI report      │    │ • Smart Checklist        │
│ • Sends via Gmail          │    │   - Critical docs        │
│                            │    │   - Project-specific     │
│ Result: Strategic brief    │    │   - Strengthen items     │
│ in user's inbox            │    │                          │
└────────────────────────────┘    │ • Readiness Score (0-100%)│
                                  │                          │
                                  │ • THREE ACTION BUTTONS:  │
                                  │   1. View Checklist      │
                                  │   2. Generate Example ⭐ │
                                  │   3. Save Progress       │
                                  └──────────────────────────┘
                                              ↓
                            Click "Generate Application Example"
                                              ↓
                                  ┌──────────────────────────┐
                                  │ APPLICATION EXAMPLE      │
                                  │                          │
                                  │ Complete 10-page mock    │
                                  │ application with:        │
                                  │                          │
                                  │ ✓ Cover page             │
                                  │ ✓ Project narrative      │
                                  │ ✓ Team & capacity        │
                                  │ ✓ Budget breakdown       │
                                  │ ✓ Milestones             │
                                  │ ✓ Supporting docs list   │
                                  │                          │
                                  │ Uses their answers       │
                                  │ + smart formatting       │
                                  │                          │
                                  │ [Download .txt file]     │
                                  └──────────────────────────┘
```

## Two Paths Explained

### PATH A: Deep Dive (Strategic Intelligence)
**Purpose:** Understand what funders really want
**Output:** AI-generated strategic brief
**Use Case:** "Help me understand SFI's priorities and how to position my project"

**What you get:**
- Funder evaluation criteria breakdown
- Red flags that cause rejection
- Strategic positioning recommendations  
- Competitive landscape insights
- Example language from successful applications

**Time:** 2-3 minutes (AI generation)
**Delivery:** Email to user

---

### PATH B: Grant Readiness (Application Preparation)
**Purpose:** Complete the actual application
**Output:** Personalized questions → Mock application
**Use Case:** "Help me fill out the SFI application form"

**What you get:**
1. **Smart Questions** - 9 questions personalized to your project
2. **Checklist** - Exactly what documents you need
3. **Readiness Score** - How prepared you are (0-100%)
4. **Application Example** - Complete mock application using your answers

**Time:** 15-30 minutes (user answers questions)
**Delivery:** Instant download

---

## Why Two Buttons Work Together

Users often need BOTH:

1. **First, click Deep Dive** → Understand the strategy
   - What does SFI really prioritize?
   - What mistakes should I avoid?
   - How should I position my project?

2. **Then, click Grant Readiness** → Complete the application
   - Answer specific questions with strategic insight
   - Generate application draft
   - Track what documents are needed

## Three-Button Layout on Grant Readiness Page

```
┌────────────────────────────────────────────────────────┐
│  Readiness Score: 85%  ✅ You're ready to apply!       │
└────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
│ 📋 View      │  │ 📄 Generate      │  │ 💾 Save      │
│ Checklist    │  │ Example ⭐       │  │ Progress     │
└──────────────┘  └──────────────────┘  └──────────────┘
       ↓                    ↓                   ↓
  Shows what          Downloads complete    Saves your
  docs needed         mock application      answers
```

## Complete Feature Set

✅ **Intake Form** - 2-minute quick capture
✅ **Matching Engine** - PRD-aligned scoring (0-100)
✅ **Deep Dive Button** - AI strategic brief (Make.com + Perplexity)
✅ **Grant Readiness Button** - Template questions + checklist
✅ **Generate Example Button** - Complete mock application
✅ **Smart Checklist** - Personalized document list
✅ **Readiness Score** - Track completion (0-100%)

## What Gets Generated (SFI Example)

**Application Example includes:**
- Cover page with contact details
- Organization eligibility proof
- Complete project narrative:
  - Duration & timeline
  - Location & forest classification
  - Activities & methods
  - Expected outcomes (forest + community)
  - Carbon/GHG benefits
  - Cultural & socioeconomic benefits
  - Scalability analysis
- Team expertise section
- Detailed budget breakdown
- Milestones & deliverables
- Measurement & monitoring plan
- Supporting documents checklist

**Length:** 8-10 pages
**Format:** Text file (.txt) - user copies into Word/PDF
**Customization:** Uses their specific answers + smart placeholders for missing info

## Testing Your New System

### Test Case 1: SFI Program
1. Fill out intake form with:
   - Applicant type: First Nation
   - Region: Barkley Sound  
   - Project: Cedar restoration
   - Budget: $250k-1M
2. Click "Find matches"
3. See SFI as top match with TWO buttons
4. Click "🔍 Deep Dive" → Gets AI strategic brief
5. Click "📋 Grant Readiness" → Answer 9 questions
6. Click "📄 Generate Example" → Download complete application

### Test Case 2: Program Without Template
1. Find match to program without template (e.g., BCSRIF)
2. "Deep Dive" button works ✓
3. "Grant Readiness" button shows "Coming Soon" (disabled)

## Next Actions

### Immediate (Test what we built):
1. **Test SFI flow end-to-end**
2. **Review generated application quality**
3. **Refine questions based on output**

### Short-term (Add more templates):
4. **Build BCSRIF template** (similar to SFI)
5. **Build FWCP template**
6. **Add templates for top 5 programs**

### Medium-term (Enhance features):
7. **Add Word doc export** (instead of just .txt)
8. **Add BCR template generator**
9. **Add budget spreadsheet template**
10. **Save/load progress to Airtable**

---

**Status:** ✅ COMPLETE - Ready to test!
**Files Updated:** 6 files
**New Features:** Grant Readiness + Application Example Generator
