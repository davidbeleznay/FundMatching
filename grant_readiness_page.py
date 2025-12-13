"""
Grant Readiness Page
Shows template-based questions and smart checklist for a specific funding program
"""

import streamlit as st
from funding_templates.template_engine import TemplateManager
from funding_templates.program_mapper import get_template_id
from application_generator import generate_sfi_application
from document_templates import generate_bcr_template, generate_chief_letter_template


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
            <p class="muted">Answer questions to see how close you are to submitting. See weak vs. strong examples for each!</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Get questions based on user's project
    questions = template.get_questions(user_intake)
    
    # Initialize responses in session state
    if 'readiness_responses' not in st.session_state:
        st.session_state.readiness_responses = {}
    
    # Calculate score upfront
    score = template.calculate_readiness_score(st.session_state.readiness_responses)
    
    # Show readiness score at top
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Readiness Score", f"{score:.0f}%")
    with col2:
        answered = len([r for r in st.session_state.readiness_responses.values() if r])
        total = len([q for q in questions if q.get('required')])
        st.metric("✅ Answered", f"{answered}/{total} required")
    with col3:
        if score >= 80:
            st.success("Ready!")
        elif score >= 50:
            st.info("Getting close")
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
                <p class="section-sub">Eligibility basics and required approvals</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    critical_questions = [q for q in questions if q['category'] == 'critical']
    for q in critical_questions:
        show_question(q, template_id, user_intake, program_name)
    
    # Readiness questions
    st.markdown(
        """
        <div class="section-header">
            <div class="section-number">2</div>
            <div>
                <h3>✓ Submission Readiness Check</h3>
                <p class="section-sub">Do you actually have what's needed to submit?</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    readiness_questions = [q for q in questions if q['category'] == 'readiness']
    for q in readiness_questions:
        show_question(q, template_id, user_intake, program_name)
    
    # Project-specific questions
    st.markdown(
        """
        <div class="section-header">
            <div class="section-number">3</div>
            <div>
                <h3>📝 Project Details</h3>
                <p class="section-sub">Technical content for your specific project</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    project_questions = [q for q in questions if q['category'] == 'project_specific']
    for q in project_questions:
        show_question(q, template_id, user_intake, program_name)
    
    # Strengthening questions
    st.markdown(
        """
        <div class="section-header">
            <div class="section-number">4</div>
            <div>
                <h3>💪 Competitive Advantages</h3>
                <p class="section-sub">Optional but significantly boost your chances</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    strengthen_questions = [q for q in questions if q['category'] == 'strengthen']
    for q in strengthen_questions:
        show_question(q, template_id, user_intake, program_name)
    
    # Bottom action bar
    st.markdown("---")
    
    # Recalculate score
    score = template.calculate_readiness_score(st.session_state.readiness_responses)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Final Score", f"{score:.0f}%")
    
    with col2:
        if st.button("📋 Checklist"):
            st.session_state.show_checklist = not st.session_state.get('show_checklist', False)
            st.rerun()
    
    with col3:
        # Generate Application Example button
        if score >= 40:
            if st.button("📄 Generate App", type="primary"):
                application_text = generate_sfi_application(
                    user_intake,
                    st.session_state.readiness_responses,
                    program
                )
                
                st.download_button(
                    label="💾 Download Application",
                    data=application_text,
                    file_name=f"SFI_Application_{user_intake.get('organization', 'Project').replace(' ', '_')}.txt",
                    mime="text/plain"
                )
        else:
            st.button(
                "📄 Generate App",
                disabled=True,
                help=f"Need 40%+ (currently {score:.0f}%)"
            )
    
    with col4:
        if st.button("← Back"):
            st.session_state.page = 'matches'
            st.rerun()
    
    # Show status interpretation
    st.markdown("")
    if score < 40:
        st.error("🔴 **Not Ready** - Missing critical items or haven't started key pieces")
        st.caption("→ Focus on Critical & Readiness sections - these are blockers")
    elif score < 60:
        st.warning("🟡 **Getting Started** - Have basics but significant work remains")
        st.caption("→ Complete all required questions, start thinking about Strengthen items")
    elif score < 80:
        st.info("🟠 **Almost Ready** - Coming together, need refinement")
        st.caption("→ Polish your answers, add competitive elements from Strengthen section")
    else:
        st.success("🟢 **Ready to Submit** - Strong, complete application!")
        st.caption("→ Final review, gather documents, and submit to SFI")
    
    # Show checklist if toggled
    if st.session_state.get('show_checklist'):
        show_checklist_section(template, user_intake)


def show_question(q: dict, template_id: str, user_intake: dict, program_name: str):
    """Display a single question with help, examples, and BCR explainer"""
    
    # Determine if answered
    response_key = f"{template_id}_{q['id']}"
    is_answered = response_key in st.session_state and st.session_state[response_key]
    
    # Add checkmark if answered
    title_prefix = "✅ " if is_answered else ""
    
    with st.expander(f"{title_prefix}**{q['question']}**", expanded=not is_answered):
        # Why we ask
        st.caption(f"**Why we ask:** {q['why']}")
        
        # BCR explainer if this is the BCR question
        if 'bcr_explainer' in q:
            st.info(q['bcr_explainer'])
            # Add BCR template download
            if st.button("📄 Download BCR Template", key=f"bcr_template_{q['id']}"):
                bcr_text = generate_bcr_template(user_intake, program_name, user_intake.get('project_title', ''))
                st.download_button(
                    label="💾 Save BCR Template",
                    data=bcr_text,
                    file_name="BCR_Template.txt",
                    mime="text/plain"
                )
        
        # Help text
        if 'help_text' in q:
            st.info(f"💡 {q['help_text']}")
        
        # Smart regional hint
        if 'hint' in q:
            st.success(f"🌍 **Hint for your region:** {q['hint']}")
        
        # Show WEAK vs STRONG examples side by side
        if 'example_weak' in q and 'example_strong' in q:
            st.markdown("**📊 Compare Weak vs. Strong Answers:**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**❌ Weak Example:**")
                st.code(q['example_weak'], language=None)
            
            with col2:
                st.markdown("**✅ Strong Example:**")
                st.code(q['example_strong'], language=None)
            
            if 'why_strong' in q:
                st.caption(f"**Why strong works:** {q['why_strong']}")
        
        # Show regular examples if no weak/strong
        elif 'examples' in q and q['examples']:
            with st.expander("💡 See examples of good answers"):
                for ex in q['examples']:
                    st.markdown(f"• {ex}")
        
        # Competitive advantage
        if 'competitive_advantage' in q:
            st.success(f"🎯 **{q['competitive_advantage']}**")
        
        # Answer input
        placeholder_text = q.get('example_strong', '') if 'example_strong' in q else ""
        
        if q.get('format') == 'List 2-4 people with: Name, Role, 1-2 sentence background':
            response = st.text_area(
                "Your answer:",
                key=response_key,
                height=150,
                help=q.get('expected_length', ''),
                placeholder="Format like the strong example above..."
            )
        else:
            response = st.text_area(
                "Your answer:",
                key=response_key,
                height=120,
                help=q.get('expected_length', ''),
                placeholder="Write your answer here (see strong example above for guidance)..."
            )
        
        # Save response and show feedback
        if response:
            st.session_state.readiness_responses[q['id']] = response
            
            # Word count
            word_count = len(response.split())
            
            # Give feedback
            if q.get('required') and word_count < 5:
                st.caption(f"⚠️ {word_count} words - add more detail (aim for {q.get('expected_length', '3-5 sentences')})")
            elif word_count < 20:
                st.caption(f"✓ {word_count} words - good start, consider adding more detail")
            else:
                st.caption(f"✓ {word_count} words - comprehensive answer!")


def show_checklist_section(template, user_intake):
    """Display the smart checklist with enhanced document help"""
    
    st.markdown("---")
    st.markdown(
        """
        <div class="section-header">
            <div class="section-number">✓</div>
            <div>
                <h3>📋 Application Checklist & Document Templates</h3>
                <p class="section-sub">Everything you need to submit</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    checklist = template.get_checklist(user_intake)
    
    # Initialize tracking
    if 'checklist_completed' not in st.session_state:
        st.session_state.checklist_completed = set()
    
    # Critical items with templates
    st.subheader("🚨 CRITICAL - Must Have Before Submitting")
    for item in checklist['critical']:
        show_checklist_item(item, user_intake, program_name=st.session_state['selected_program'].get('Program_Name'))
    
    # Project-specific
    if checklist['project_specific']:
        st.subheader("📝 PROJECT-SPECIFIC REQUIREMENTS")
        for item in checklist['project_specific']:
            show_checklist_item(item, user_intake)
    
    # Strengthen
    st.subheader("💪 STRENGTHEN APPLICATION (Optional)")
    st.caption("Not required but significantly improve your chances")
    for item in checklist['strengthen']:
        show_checklist_item(item, user_intake, optional=True)
    
    # Summary metrics
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


def show_checklist_item(item: dict, user_intake: dict, program_name: str = None, optional: bool = False):
    """Display checklist item with template download if available"""
    
    col1, col2 = st.columns([0.08, 0.92])
    
    with col1:
        item_key = f"check_{item['item']}"
        checked = st.checkbox("", key=item_key, label_visibility="collapsed")
        
        if checked:
            st.session_state.checklist_completed.add(item['item'])
        elif item['item'] in st.session_state.checklist_completed:
            st.session_state.checklist_completed.remove(item['item'])
    
    with col2:
        # Item name
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
        
        # Explainer for BCR
        if 'explainer' in item:
            st.caption(f"ℹ️ {item['explainer']}")
        
        # How to get
        if 'how_to_get' in item:
            st.caption(f"📍 How: {item['how_to_get']}")
        if 'where_to_find' in item:
            st.caption(f"📍 Where: {item['where_to_find']}")
        
        # Template download buttons
        if item.get('template_available'):
            if 'Band Council Resolution' in item['item']:
                if st.button("📄 Get BCR Template", key=f"dl_bcr_{item['item']}"):
                    bcr = generate_bcr_template(user_intake, program_name or "SFI Program", user_intake.get('project_title', ''))
                    st.download_button(
                        "💾 Download BCR",
                        data=bcr,
                        file_name="BCR_Template.txt",
                        mime="text/plain",
                        key=f"save_bcr_{item['item']}"
                    )
            
            elif 'Letter' in item['item'] and 'Chief' in item['item']:
                if st.button("📄 Get Letter Template", key=f"dl_letter_{item['item']}"):
                    letter = generate_chief_letter_template(user_intake, program_name or "SFI Program")
                    st.download_button(
                        "💾 Download Letter",
                        data=letter,
                        file_name="Chief_Letter_Template.txt",
                        mime="text/plain",
                        key=f"save_letter_{item['item']}"
                    )
        
        st.markdown("")  # Spacing
