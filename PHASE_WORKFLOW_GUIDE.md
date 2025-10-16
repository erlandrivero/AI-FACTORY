# Phase-Based Workflow Implementation Guide

## Overview
This guide shows how to refactor `app.py` to use explicit phase tracking with `st.session_state.phase`.

## Phases
1. **idea_input** - User enters project idea and uploads files
2. **strategy_selection** - User reviews AI consultation and selects options  
3. **info_gathering** - User provides API keys/configuration
4. **building** - AI crew builds the project
5. **complete** - Display final results

## Key Changes

### 1. Initialize Phase State (add after line 1260)
```python
if 'phase' not in st.session_state:
    st.session_state.phase = 'idea_input'
if 'project_idea' not in st.session_state:
    st.session_state.project_idea = ""
if 'uploaded_files_data' not in st.session_state:
    st.session_state.uploaded_files_data = []
if 'deliverables_config' not in st.session_state:
    st.session_state.deliverables_config = {
        'code': True, 'deployment': True, 'docs': True, 'tests': False
    }
if 'process_type' not in st.session_state:
    st.session_state.process_type = 'Hierarchical'
if 'api_keys_collected' not in st.session_state:
    st.session_state.api_keys_collected = {}
```

### 2. Add Phase Progress Indicator (add after line 1293)
```python
# Show phase progress indicator
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
```

### 3. Restructure Content with Phase Blocks

Replace the current linear flow (lines 1295-1906) with:

```python
# ============================================================================
# PHASE 1: IDEA INPUT
# ============================================================================
if st.session_state.phase == 'idea_input':
    st.subheader("💡 Step 1: Describe Your Project")
    
    idea = st.text_area("Project Idea", value=st.session_state.project_idea, height=220)
    # ... file upload logic ...
    
    if st.button("💡 Get Consultation", disabled=not bool(idea.strip())):
        st.session_state.project_idea = idea.strip()
        # ... run consultation ...
        st.session_state.phase = 'strategy_selection'
        st.rerun()

# ============================================================================
# PHASE 2: STRATEGY SELECTION
# ============================================================================
elif st.session_state.phase == 'strategy_selection':
    st.subheader("🎯 Step 2: Choose Your Strategy")
    
    # Show consultation results
    st.markdown(st.session_state.consultation_result)
    
    # Selection UI
    tech_choice = st.radio("Tech Stack", ["Option A", "Option B", "Option C"])
    platform_choice = st.selectbox("Platform", ["Vercel", "Netlify", ...])
    # ... deliverables checkboxes ...
    
    if st.button("➡️ Continue to Config"):
        st.session_state.user_selections = {'tech': tech_choice, 'platform': platform_choice}
        st.session_state.deliverables_config = {...}
        st.session_state.phase = 'info_gathering'
        st.rerun()

# ============================================================================
# PHASE 3: INFO GATHERING
# ============================================================================
elif st.session_state.phase == 'info_gathering':
    st.subheader("🔐 Step 3: Configuration & API Keys")
    
    with st.form("api_keys_form"):
        openai_key = st.text_input("OpenAI API Key", type="password")
        database_url = st.text_input("Database URL", type="password")
        
        if st.form_submit_button("💾 Save & Continue"):
            st.session_state.api_keys_collected = {...}
            st.session_state.phase = 'building'
            st.rerun()
    
    if st.button("⏭️ Skip & Build"):
        st.session_state.phase = 'building'
        st.rerun()

# ============================================================================
# PHASE 4: BUILDING
# ============================================================================
elif st.session_state.phase == 'building':
    st.subheader("🚀 Step 4: Building Your Project")
    
    # ... existing crew execution logic (lines 1556-1906) ...
    # After successful build:
    st.session_state.phase = 'complete'
    st.rerun()

# ============================================================================
# PHASE 5: COMPLETE
# ============================================================================
elif st.session_state.phase == 'complete':
    st.subheader("✅ Step 5: Your Project is Ready!")
    
    # ... existing results display logic (lines 1910-2370) ...
    
    if st.button("🔄 Start New Project"):
        st.session_state.phase = 'idea_input'
        st.session_state.execution_result = None
        st.rerun()
```

### 4. Update Building Phase Completion

In the crew execution success block (around line 1886), add:

```python
# After storing execution results:
st.session_state.execution_result = result
st.session_state.execution_metadata = {...}

# Move to complete phase
st.session_state.phase = 'complete'
st.rerun()
```

### 5. Add Reset Functionality

For "Start Over" buttons, use:

```python
if st.button("🔄 Start Over"):
    st.session_state.phase = 'idea_input'
    st.session_state.consultation_result = None
    st.session_state.user_selections = {}
    st.session_state.execution_result = None
    st.rerun()
```

## Benefits

✅ **Clear state machine** - Easy to understand where user is in process
✅ **Better UX** - Visual progress indicator
✅ **Flexible navigation** - Can go back/forward between phases
✅ **Persistent state** - All choices saved in session state
✅ **Modular code** - Each phase is self-contained

## Implementation Steps

1. Backup current `app.py`
2. Add new session state variables
3. Add phase progress indicator
4. Wrap each section in `if st.session_state.phase == '...':`
5. Add phase transition buttons
6. Test each phase independently
7. Test full workflow end-to-end

## Testing Checklist

- [ ] Phase 1: Can enter idea and get consultation
- [ ] Phase 2: Can select options and proceed
- [ ] Phase 3: Can skip or enter API keys
- [ ] Phase 4: Crew executes successfully
- [ ] Phase 5: Results display correctly
- [ ] Back buttons work
- [ ] Start over resets all state
- [ ] Progress indicator updates correctly
