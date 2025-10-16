# Quick Integration Steps for Phase-Based Workflow

## Summary
Transform your existing `project_execution_page()` function into a phase-based workflow with minimal changes.

## Files Created
1. **PHASE_WORKFLOW_GUIDE.md** - Complete conceptual guide
2. **phase_workflow_example.py** - Full working example  
3. **INTEGRATION_STEPS.md** - This file (quick reference)

## Minimal Integration Approach

### Option 1: Quick Fix (15 minutes)
Just add phase tracking to existing flow:

1. **Add to session state init (after line 1260):**
```python
if 'phase' not in st.session_state:
    st.session_state.phase = 'idea_input'
```

2. **Add progress indicator (after line 1293):**
```python
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

3. **Update phase transitions:**
- After consultation success (line ~1542): `st.session_state.phase = 'strategy_selection'`
- When user clicks "Build Project" (line ~1414): `st.session_state.phase = 'building'`
- After successful build (line ~1888): `st.session_state.phase = 'complete'`

4. **Add conditional display (wrap existing sections):**
```python
# Around line 1295
if st.session_state.phase in ['idea_input', 'strategy_selection']:
    # ... existing idea input and consultation code ...
    pass

if st.session_state.phase == 'strategy_selection':
    # ... existing strategy selection code ...
    pass

if st.session_state.phase in ['building', 'complete']:
    # ... existing crew execution and results ...
    pass
```

### Option 2: Full Refactor (1-2 hours)
Replace entire function with phase_workflow_example.py structure.

## What to Test

### Phase 1 (idea_input)
- [ ] Can enter project idea
- [ ] Can upload files
- [ ] "Get Consultation" button works
- [ ] Transitions to strategy_selection

### Phase 2 (strategy_selection)  
- [ ] Consultation results display
- [ ] Can select tech stack
- [ ] Can select platform
- [ ] Can choose deliverables
- [ ] Transitions to info_gathering (or skip to building)

### Phase 3 (info_gathering)
- [ ] API key form displays
- [ ] Can enter keys
- [ ] Can skip
- [ ] Transitions to building

### Phase 4 (building)
- [ ] Shows spinner
- [ ] Crew executes
- [ ] Progress updates
- [ ] Transitions to complete

### Phase 5 (complete)
- [ ] Results display
- [ ] Download buttons work
- [ ] Deployment section shows
- [ ] "Start New" resets to idea_input

## Quick Commands

```bash
# Backup original
cp app.py app.py.backup

# Test changes
streamlit run app.py

# If issues, restore
cp app.py.backup app.py
```

## Key Session State Variables

```python
st.session_state.phase              # Current workflow phase
st.session_state.project_idea       # User's project description
st.session_state.uploaded_files_data  # Parsed file data
st.session_state.consultation_result  # AI consultation text
st.session_state.user_selections    # Tech/platform choices
st.session_state.deliverables_config  # What to build
st.session_state.process_type       # Hierarchical/Sequential/Consensus
st.session_state.api_keys_collected # User-provided API keys
st.session_state.execution_result   # Final crew output
st.session_state.execution_metadata # Duration, timestamp, etc.
```

## Common Issues & Fixes

### Issue: Phase doesn't change
**Fix:** Make sure you call `st.rerun()` after setting `st.session_state.phase`

### Issue: Lost data between phases
**Fix:** Store everything in `st.session_state`, not local variables

### Issue: Progress indicator wrong
**Fix:** Check that phase name exactly matches one of the 5 phases

### Issue: Can't go back
**Fix:** Add back buttons that set phase to previous phase + st.rerun()

## Next Steps

1. ✅ Read PHASE_WORKFLOW_GUIDE.md for concepts
2. ✅ Review phase_workflow_example.py for complete code
3. ⚡ Choose Option 1 (quick) or Option 2 (full)
4. 🧪 Test each phase independently  
5. 🎉 Deploy updated app

## Need Help?

- Check session state values with: `st.write(st.session_state)`
- Add debug output: `st.info(f"Current phase: {st.session_state.phase}")`
- Test locally before deploying

---

**Estimated Time:**
- Option 1: 15-30 minutes
- Option 2: 1-2 hours
- Testing: 30 minutes
