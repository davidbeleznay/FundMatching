"""
Grant Readiness Page
Shows template-based questions and smart checklist for a specific funding program
"""

import streamlit as st
from funding_templates.template_engine import TemplateManager
from funding_templates.program_mapper import get_template_id
from application_generator import generate_sfi_application


def show_grant_readiness_page():
    """Display the grant readiness questions and checklist"""
    
    # Get program details from session state
    if 'selected_program' not in st.session_state:
        st.error("No program selected. Please go back and select a funding match.")
        if st.button("← Back to matches"):
            st.session_state.page = 'matches'
            st.rerun()
        return
    
    program = st.session_state['selected_program']
    program_name = program.get('Program_Name', 'Unknown Program')
    
    # Get user intake data
    user_intake = st.session_state.get('user_intake', {})
    
    # Try to load template
    template_id = get_template_id(program_name)
    
    if not template_id:
        st.warning(f"⚠️ Grant Readiness template not yet available for **{program_name}**")
        st.info("This feature is being built out program by program. Check back soon!")
        if st.button("← Back to matches"):
            st.session_state.page = 'matches'
            st.rerun()
        return
    
    # Load template
    tm = TemplateManager()
    template = tm.get_template(template_id)
    
    if not template:
        st.error(f"Could not load template: {template_id}")
        return
    
    # Header
    st.markdown(
        f"""
        <div class="hero">
            <p class="eyebrow">Grant Readiness Assessment</p>
            <h1>🎯 {program_name}</h1>
            <p class="muted">Answer these questions to see how close you are to submitting a strong application.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Get questions based on user's project
    questions = template.get_questions(user_intake)
    
    # Initialize responses in session state
    if 'readiness_responses' not in st.session_state:
        st.session_state.readiness_responses = {}
    
    # Calculate score upfront to show progress
    score = template.calculate_readiness_score(st.session_state.readiness_responses)
    
    # Show readiness score at top
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Readiness Score", f"{score:.0f}%")
    with col2:
        answered = len([r for r in st.session_state.readiness_responses.values() if r])
        total = len([q for q in questions if q.get('required')])
        st.metric("✅ Questions Answered", f"{answered}/{total}")
    with col3:
        if score >= 80:
            st.success("Ready to apply!")
        elif score >= 50:
            st.info("Getting close...")
        else:
            st.warning("Needs work")
    
    # Display questions by category
    st.markdown("---")
    
    # Critical questions
    st.markdown(
        """
        <div class="section-header">
            <div class="section-number">1</div>
            <div>
                <h3>🚨 Critical Requirements</h3>
                <p class="section-sub">Must-haves for your application - start here</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    critical_questions = [q for q in questions if q['category'] == 'critical']
    for q in critical_questions:
        show_question(q, template_id)
    
    # Readiness/Status questions (NEW CATEGORY!)
    st.markdown(
        """
        <div class="section-header">
            <div class="section-number">2</div>
            <div>
                <h3>✓ Application Readiness Status</h3>
                <p class="section-sub">Do you actually have what's needed to submit?</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    readiness_questions = [q for q in questions if q['category'] == 'readiness']
    if readiness_questions:
        for q in readiness_questions:
            show_question(q, template_id)
    else:
        st.info("No readiness check questions for this program yet")
    
    # Project-specific questions
    st.markdown(
        """
        <div class="section-header">
            <div class="section-number">3</div>
            <div>
                <h3>📝 Project-Specific Details</h3>
                <p class="section-sub">Information specific to your project and approach</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    project_questions = [q for q in questions if q['category'] == 'project_specific']
    for q in project_questions:
        show_question(q, template_id)
    
    # Strengthening questions
    st.markdown(
        """
        <div class="section-header">
            <div class="section-number">4</div>
            <div>
                <h3>💪 Strengthen Your Application</h3>
                <p class="section-sub">Optional but highly recommended - these improve competitiveness</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    strengthen_questions = [q for q in questions if q['category'] == 'strengthen']
    for q in strengthen_questions:
        show_question(q, template_id)
    
    # Bottom action bar
    st.markdown("---")
    
    # Recalculate score
    score = template.calculate_readiness_score(st.session_state.readiness_responses)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Final Score", f"{score:.0f}%")
    
    with col2:
        if st.button("📋 View Checklist"):
            st.session_state.show_checklist = not st.session_state.get('show_checklist', False)
            st.rerun()
    
    with col3:
        # Generate Application Example button
        if score >= 40:
            if st.button("📄 Generate Example", type="primary"):
                application_text = generate_sfi_application(
                    user_intake,
                    st.session_state.readiness_responses,
                    program
                )
                
                # Offer download
                st.download_button(
                    label="💾 Download Application",
                    data=application_text,
                    file_name=f"SFI_Application_{user_intake.get('organization', 'Project').replace(' ', '_')}.txt",
                    mime="text/plain"
                )
        else:
            st.button(
                "📄 Generate Example",
                disabled=True,
                help=f"Answer more questions to unlock (need 40%+ readiness, currently {score:.0f}%)"
            )
    
    with col4:
        if st.button("← Back"):
            st.session_state.page = 'matches'
            st.rerun()
    
    # Show readiness interpretation
    st.markdown("")
    if score < 40:
        st.error("🔴 **Not Ready** - Significant work needed before you can submit")
        st.caption("Focus on Critical and Readiness sections first")
    elif score < 60:
        st.warning("🟡 **Getting Started** - You have the basics but need more detail")
        st.caption("Complete Project-Specific questions and start on Strengthen items")
    elif score < 80:
        st.info("🟠 **Almost Ready** - Application is coming together, refine and strengthen")
        st.caption("Review all answers, add Strengthen items to improve competitiveness")
    else:
        st.success("🟢 **Ready to Submit** - You have a strong, complete application!")
        st.caption("Do final review, gather supporting documents, and submit")
    
    # Show checklist if toggled
    if st.session_state.get('show_checklist'):
        show_checklist_section(template, user_intake)


def show_question(q: dict, template_id: str):
    """Display a single question with help text and examples"""
    
    # Determine if question is answered
    response_key = f"{template_id}_{q['id']}"
    is_answered = response_key in st.session_state and st.session_state[response_key]
    
    # Add checkmark to title if answered
    title_prefix = "✅ " if is_answered else ""
    
    with st.expander(f"{title_prefix}**{q['question']}**", expanded=not is_answered):
        # Why we ask
        st.caption(f"**Why we ask:** {q['why']}")
        
        # Help text
        if 'help_text' in q:
            st.info(q['help_text'])
        
        # Smart hint (region-specific)
        if 'hint' in q:
            st.success(f"💡 **Hint for your region:** {q['hint']}")
        
        # Examples
        if 'examples' in q and q['examples']:
            with st.expander("💡 See examples"):
                for ex in q['examples']:
                    st.markdown(f"• {ex}")
        
        # Competitive advantage callout
        if 'competitive_advantage' in q:
            st.success(f"🎯 **{q['competitive_advantage']}**")
        
        # Answer input
        if q.get('format') == 'List 2-4 people with: Name, Role, 1-2 sentence background':
            response = st.text_area(
                "Your answer:",
                key=response_key,
                height=150,
                help=q.get('expected_length', ''),
                placeholder="Example:\\n• Sarah Johnson, RPF - Lands Manager, 15 years experience...\\n• Elder Tom George - Cultural advisor..."
            )
        else:
            response = st.text_area(
                "Your answer:",
                key=response_key,
                height=120,
                help=q.get('expected_length', '')
            )
        
        # Save response
        if response:
            st.session_state.readiness_responses[q['id']] = response
            
            # Show word count for required fields
            word_count = len(response.split())
            if q.get('required') and word_count < 5:
                st.caption(f"⚠️ {word_count} words - add a bit more detail")
            else:
                st.caption(f"✓ {word_count} words")


def show_checklist_section(template, user_intake):
    """Display the smart checklist"""
    
    st.markdown("---")
    st.markdown(
        """
        <div class="section-header">
            <div class="section-number">✓</div>
            <div>
                <h3>📋 Your Application Checklist</h3>
                <p class="section-sub">Documents and tasks you'll need to submit</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    checklist = template.get_checklist(user_intake)
    
    # Initialize checklist completion tracking
    if 'checklist_completed' not in st.session_state:
        st.session_state.checklist_completed = set()
    
    # Critical items
    st.subheader("🚨 CRITICAL - Must Have Before Applying")
    for item in checklist['critical']:
        show_checklist_item(item)
    
    # Project-specific
    if checklist['project_specific']:
        st.subheader("📝 PROJECT-SPECIFIC REQUIREMENTS")
        for item in checklist['project_specific']:
            show_checklist_item(item)
    
    # Strengthen
    st.subheader("💪 STRENGTHEN YOUR APPLICATION (Optional)")
    st.caption("These aren't required but significantly improve competitiveness")
    for item in checklist['strengthen']:
        show_checklist_item(item, optional=True)
    
    # Time estimate
    completed = st.session_state.checklist_completed
    weeks_remaining = template.estimate_time_to_ready(checklist, completed)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        total_items = len(checklist['critical']) + len(checklist['project_specific']) + len(checklist['strengthen'])
        progress = len(completed) / total_items if total_items > 0 else 0
        st.metric("Checklist Progress", f"{len(completed)}/{total_items} items")
        st.progress(progress)
    
    with col2:
        st.metric("⏱️ Estimated Time to Ready", f"{weeks_remaining:.0f} weeks")


def show_checklist_item(item: dict, optional: bool = False):
    """Display a single checklist item"""
    
    col1, col2 = st.columns([0.08, 0.92])
    
    with col1:
        item_key = f"check_{item['item']}"
        checked = st.checkbox("", key=item_key, label_visibility="collapsed")
        
        if checked:
            st.session_state.checklist_completed.add(item['item'])
        elif item['item'] in st.session_state.checklist_completed:
            st.session_state.checklist_completed.remove(item['item'])
    
    with col2:
        # Item name with optional indicator
        if optional:
            st.markdown(f"**{item['item']}** _(optional)_")
        else:
            st.markdown(f"**{item['item']}**")
        
        # Details
        details = []
        if 'time_estimate' in item:
            details.append(f"⏱️ {item['time_estimate']}")
        if 'why' in item:
            details.append(item['why'])
        if 'impact' in item:
            details.append(f"Impact: {item['impact']}")
        
        if details:
            st.caption(" • ".join(details))
        
        # Additional help
        if 'how_to_get' in item:
            st.caption(f"📍 How to get: {item['how_to_get']}")
        if 'where_to_find' in item:
            st.caption(f"📍 Where to find: {item['where_to_find']}")
        if 'template_available' in item and item['template_available']:
            st.caption("📄 Template available - [Download](#)")
        
        st.markdown("")  # Spacing
