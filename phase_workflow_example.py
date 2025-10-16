# Example Phase-Based Workflow for project_execution_page()
# This is a simplified structure showing the pattern
# Integrate this pattern into your existing app.py

def project_execution_page():
    st.header("🚀 Project Execution")
    st.write("Build complete applications with AI-powered agents.")

    # ========================================================================
    # INITIALIZE SESSION STATE
    # ========================================================================
    if 'phase' not in st.session_state:
        st.session_state.phase = 'idea_input'
    if 'project_idea' not in st.session_state:
        st.session_state.project_idea = ""
    if 'uploaded_files_data' not in st.session_state:
        st.session_state.uploaded_files_data = []
    if 'consultation_result' not in st.session_state:
        st.session_state.consultation_result = None
    if 'user_selections' not in st.session_state:
        st.session_state.user_selections = {}
    if 'deliverables_config' not in st.session_state:
        st.session_state.deliverables_config = {'code': True, 'deployment': True, 'docs': True, 'tests': False}
    if 'process_type' not in st.session_state:
        st.session_state.process_type = 'Hierarchical'
    if 'api_keys_collected' not in st.session_state:
        st.session_state.api_keys_collected = {}
    if 'execution_result' not in st.session_state:
        st.session_state.execution_result = None
    if 'execution_metadata' not in st.session_state:
        st.session_state.execution_metadata = {}
    
    # ========================================================================
    # PHASE PROGRESS INDICATOR
    # ========================================================================
    phases = ['idea_input', 'strategy_selection', 'info_gathering', 'building', 'complete']
    phase_names = ['💡 Idea', '🎯 Strategy', '🔐 Config', '🚀 Building', '✅ Complete']
    current_phase_idx = phases.index(st.session_state.phase) if st.session_state.phase in phases else 0
    
    cols = st.columns(len(phases))
    for idx, (col, phase_name) in enumerate(zip(cols, phase_names)):
        with col:
            if idx < current_phase_idx:
                st.success(f"✓ {phase_name}")
            elif idx == current_phase_idx:
                st.info(f"▶ {phase_name}")
            else:
                st.caption(phase_name)
    
    st.divider()
    
    # ========================================================================
    # PHASE 1: IDEA INPUT
    # ========================================================================
    if st.session_state.phase == 'idea_input':
        st.subheader("💡 Step 1: Describe Your Project")
        
        idea = st.text_area(
            "Project Idea",
            value=st.session_state.project_idea,
            height=220,
            placeholder="Describe what you want to build..."
        )
        
        # File uploads (reuse your existing parse_uploaded_file logic)
        uploaded_files = st.file_uploader(
            "Upload Background Materials (Optional)",
            type=['ipynb', 'md', 'csv', 'txt', 'py', 'json'],
            accept_multiple_files=True
        )
        
        files_data = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                parsed = parse_uploaded_file(uploaded_file)
                files_data.append(parsed)
                st.info(f"{parsed['icon']} {parsed['name']}")
        
        st.divider()
        
        if st.button("💡 Get Consultation", type="primary", disabled=not bool(idea.strip())):
            st.session_state.project_idea = idea.strip()
            st.session_state.uploaded_files_data = files_data
            
            # Run consultation (reuse your existing consultation logic)
            with st.spinner("🤔 Orchestrator analyzing..."):
                # ... your consultation crew logic here ...
                # consultation_result = consult_crew.kickoff()
                # st.session_state.consultation_result = str(consultation_result.raw)
                pass
            
            # Move to next phase
            st.session_state.phase = 'strategy_selection'
            st.rerun()
    
    # ========================================================================
    # PHASE 2: STRATEGY SELECTION
    # ========================================================================
    elif st.session_state.phase == 'strategy_selection':
        st.subheader("🎯 Step 2: Choose Your Strategy")
        
        # Show consultation
        if st.session_state.consultation_result:
            with st.expander("📊 Consultation Results", expanded=True):
                st.markdown(st.session_state.consultation_result)
        
        st.divider()
        
        # Selections
        col1, col2 = st.columns(2)
        with col1:
            tech_choice = st.radio("Tech Stack", ["Option A", "Option B", "Option C", "Custom"])
        with col2:
            platform_choice = st.selectbox("Platform", ["Vercel", "Netlify", "Railway", "As recommended"])
        
        # Deliverables
        st.subheader("📦 Deliverables")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            include_code = st.checkbox("✅ Code files", value=True)
            include_deployment = st.checkbox("📋 Deployment", value=True)
        with col_d2:
            include_docs = st.checkbox("📚 Documentation", value=True)
            include_tests = st.checkbox("🧪 Tests", value=False)
        
        # Process type
        process_type = st.selectbox("Process Type", ["Hierarchical", "Sequential", "Consensus"])
        
        st.divider()
        
        col_a1, col_a2, col_a3 = st.columns([1, 1, 1])
        with col_a1:
            if st.button("← Back"):
                st.session_state.phase = 'idea_input'
                st.rerun()
        with col_a3:
            if st.button("Continue →", type="primary"):
                st.session_state.user_selections = {
                    'tech': tech_choice,
                    'platform': platform_choice
                }
                st.session_state.deliverables_config = {
                    'code': include_code,
                    'deployment': include_deployment,
                    'docs': include_docs,
                    'tests': include_tests
                }
                st.session_state.process_type = process_type
                st.session_state.phase = 'info_gathering'
                st.rerun()
    
    # ========================================================================
    # PHASE 3: INFO GATHERING
    # ========================================================================
    elif st.session_state.phase == 'info_gathering':
        st.subheader("🔐 Step 3: Configuration & API Keys")
        
        with st.expander("📋 Your Selections"):
            st.write(f"**Tech:** {st.session_state.user_selections.get('tech')}")
            st.write(f"**Platform:** {st.session_state.user_selections.get('platform')}")
            st.write(f"**Process:** {st.session_state.process_type}")
        
        st.divider()
        
        with st.form("api_keys_form"):
            st.info("💡 Optional: Provide API keys for your project")
            
            openai_key = st.text_input("OpenAI API Key", type="password")
            database_url = st.text_input("Database URL", type="password")
            other_keys = st.text_area("Other Keys (KEY=value format)")
            
            submitted = st.form_submit_button("💾 Save & Continue", type="primary")
            
            if submitted:
                api_keys = {}
                if openai_key:
                    api_keys['OPENAI_API_KEY'] = openai_key
                if database_url:
                    api_keys['DATABASE_URL'] = database_url
                # Parse other_keys...
                
                st.session_state.api_keys_collected = api_keys
                st.session_state.phase = 'building'
                st.rerun()
        
        col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
        with col_b1:
            if st.button("← Back"):
                st.session_state.phase = 'strategy_selection'
                st.rerun()
        with col_b3:
            if st.button("Skip & Build →"):
                st.session_state.phase = 'building'
                st.rerun()
    
    # ========================================================================
    # PHASE 4: BUILDING
    # ========================================================================
    elif st.session_state.phase == 'building':
        st.subheader("🚀 Step 4: Building Your Project")
        
        with st.expander("📋 Build Config"):
            st.write(f"**Idea:** {st.session_state.project_idea[:100]}...")
            st.write(f"**Tech:** {st.session_state.user_selections.get('tech')}")
            st.write(f"**Platform:** {st.session_state.user_selections.get('platform')}")
        
        st.divider()
        
        # BUILD EXECUTION LOGIC
        # Reuse your existing crew building logic (lines 1556-1906)
        # Key changes:
        # 1. Get data from session state instead of local variables
        # 2. After successful build, transition to 'complete' phase
        
        # Example structure:
        try:
            # ... your existing crew setup ...
            # crew = Crew(agents=crew_agents, tasks=tasks, process=crew_process)
            
            with st.spinner("🚀 Crew working..."):
                # ... crew.kickoff() ...
                # result = crew.kickoff()
                pass
            
            # Store results
            # st.session_state.execution_result = result
            # st.session_state.execution_metadata = {...}
            
            # Move to completion phase
            st.session_state.phase = 'complete'
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Build failed: {e}")
            if st.button("🔄 Try Again"):
                st.rerun()
    
    # ========================================================================
    # PHASE 5: COMPLETE
    # ========================================================================
    elif st.session_state.phase == 'complete':
        st.subheader("✅ Step 5: Your Project is Ready!")
        
        # Show execution info
        if st.session_state.execution_metadata:
            cols = st.columns(4)
            with cols[0]:
                st.metric("⏱️ Duration", format_time(st.session_state.execution_metadata.get('elapsed_time', 0)))
            with cols[1]:
                st.metric("🎯 Process", st.session_state.execution_metadata.get('process_type', 'N/A'))
            with cols[2]:
                st.metric("🚀 Platform", st.session_state.execution_metadata.get('platform', 'N/A'))
            with cols[3]:
                st.metric("📅 Completed", st.session_state.execution_metadata.get('timestamp', 'N/A'))
        
        st.divider()
        
        # Display results (reuse your existing result display logic lines 1939-2092)
        if st.session_state.execution_result:
            result = st.session_state.execution_result
            
            # Get result text
            if isinstance(result, str):
                result_text = result
            else:
                result_text = str(getattr(result, 'raw', getattr(result, 'output', str(result))))
            
            st.markdown(result_text)
            
            # Export options
            st.subheader("💾 Export Options")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    "📄 Download MD",
                    data=result_text,
                    file_name=f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            
            with col2:
                # Extract and download code files as ZIP
                code_files = extract_code_files_from_result(result_text)
                if code_files:
                    zip_data = create_project_zip(code_files, "project")
                    st.download_button(
                        f"📦 ZIP ({len(code_files)} files)",
                        data=zip_data,
                        file_name=f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip"
                    )
            
            with col3:
                st.download_button(
                    "📝 Download TXT",
                    data=result_text,
                    file_name=f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        st.divider()
        
        # Deployment section (reuse your existing deployment logic lines 2097-2370)
        st.header("🚀 Deploy Your App")
        # ... your existing deployment recommendation code ...
        
        st.divider()
        
        # Action buttons
        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        with col_f2:
            if st.button("🔄 Start New Project", type="primary", use_container_width=True):
                # Reset to beginning
                st.session_state.phase = 'idea_input'
                st.session_state.execution_result = None
                st.session_state.execution_metadata = {}
                st.session_state.consultation_result = None
                st.session_state.user_selections = {}
                st.session_state.project_idea = ""
                st.rerun()
