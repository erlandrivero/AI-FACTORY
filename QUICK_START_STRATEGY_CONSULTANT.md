# Quick Start: Strategy Consultant Integration

## ⚡ Get Started in 3 Steps

### Step 1: Add the Strategy Consultant Agent

1. **Go to Agent Management page** in the app
2. **Click "Create a New Agent"**
3. **Copy the profile** from `strategy_consultant_agent_example.json`
4. **Fill in the form:**
   - **Role:** `Strategy Consultant Agent`
   - **Goal:** (copy from example file)
   - **Backstory:** (copy from example file)
   - **Allow Delegation:** ❌ Uncheck (false)
5. **Click "💾 Save Agent"**

### Step 2: Test the New Workflow

1. **Go to Project Execution page**
2. **You should see the phase indicator:**
   ```
   ▶ 💡 Idea  |  🎯 Strategy  |  🔐 Config  |  🚀 Building  |  ✅ Complete
   ```
3. **Enter a project idea**, for example:
   ```
   I want to build a task management app where users can create projects,
   add tasks with due dates, assign tasks to team members, and track progress
   with a dashboard. Users should be able to sign up, log in, and collaborate
   in real-time.
   ```
4. **Click "🎯 Plan Strategy"**
5. **Wait for Strategy Consultant** to analyze (15-30 seconds)
6. **Review the solution packages** presented

### Step 3: Make Selections and Build

1. **Choose your preferred package** (A, B, or C)
2. **Select deployment platform**
3. **Configure deliverables** (code, deployment, docs, tests)
4. **Click "Continue to Building →"**
5. **The existing build workflow** will execute

## 🎯 Expected Behavior

### Phase 1: Idea Input
- ✅ Shows "Step 1: Describe Your Project"
- ✅ Has text area for project idea
- ✅ Has optional file upload section
- ✅ Has "🎯 Plan Strategy" button (NOT "Get Consultation")
- ✅ Button is disabled when idea is empty

### Phase 2: Strategy Selection
- ✅ Shows "Step 2: Choose Your Solution Package"
- ✅ Displays solution packages in expandable section
- ✅ Has radio buttons for "Package A/B/C/Custom" (NOT "Option A/B/C")
- ✅ Has platform dropdown
- ✅ Has deliverables checkboxes
- ✅ Has "← Back to Idea" button
- ✅ Has "Continue to Building →" button

### Phase 3+: Building & Results
- ✅ Existing workflow continues
- ✅ Crew execution happens
- ✅ Results display with download options

## 🐛 Troubleshooting

### Error: "Strategy Consultant Agent not found"
**Solution:** Create an agent with "Strategy Consultant" in the role name (case-insensitive)

### Phase indicator doesn't show
**Solution:** Refresh the page - session state should initialize on load

### "Plan Strategy" button stays disabled
**Solution:** Make sure you've typed something in the project idea text area

### Solution packages don't display
**Solution:** Check the session state debug info:
```python
st.write(st.session_state.strategy_options)
```
If it's `None`, the Strategy Consultant didn't run successfully

### Can't navigate between phases
**Solution:** Make sure `st.rerun()` is being called after phase transitions

## 📋 Test Scenarios

### Scenario 1: Simple App
```
Idea: "A weather app that shows current weather and 5-day forecast"
Expected: 3 packages with varying complexity (React+API, Next.js+Vercel, etc.)
```

### Scenario 2: Full-Stack App
```
Idea: "An e-commerce platform with product catalog, shopping cart, 
user authentication, and payment processing"
Expected: 3 packages with complete stacks (MERN, Next.js+Supabase, etc.)
```

### Scenario 3: Data-Heavy App
```
Idea: "A data visualization dashboard that connects to CSV files 
and displays interactive charts"
Expected: 3 packages considering data processing (Streamlit, React+D3, etc.)
```

## 🔍 Debug Mode

Add this to any phase to see current state:
```python
with st.expander("🔍 Debug Info"):
    st.write("**Current Phase:**", st.session_state.phase)
    st.write("**Project Idea:**", st.session_state.project_idea[:100] + "...")
    st.write("**Has Strategy Options:**", st.session_state.strategy_options is not None)
    st.write("**User Selections:**", st.session_state.user_selections)
```

## ✅ Success Indicators

You know it's working when:
1. ✅ Strategy Consultant runs independently (not Orchestrator)
2. ✅ Solution packages are stored in `st.session_state.strategy_options`
3. ✅ Phase transitions happen automatically (idea_input → strategy_selection)
4. ✅ Back button returns to idea_input phase
5. ✅ Continue button moves to building phase with all selections saved

## 🎉 What's New vs Old Workflow

### Old Workflow
- Used Orchestrator for consultation
- "Get Consultation" button
- "Option A/B/C" selection
- No clear phase separation

### New Workflow
- Uses **Strategy Consultant** (specialized agent)
- "Plan Strategy" button
- "Package A/B/C" selection (clearer naming)
- **Phase-based** with visual progress indicator
- Can **go back** to revise idea
- Selections **persist** across navigation

## 📚 Files to Reference

1. **STRATEGY_CONSULTANT_UPDATE.md** - Complete technical documentation
2. **strategy_consultant_agent_example.json** - Agent profile example
3. **PHASE_WORKFLOW_GUIDE.md** - General phase workflow concepts
4. **phase_workflow_example.py** - Full example implementation

## 🚀 Next Actions

After confirming this works:
1. Test with various project ideas
2. Refine Strategy Consultant agent profile if needed
3. Consider implementing remaining phases (info_gathering, etc.)
4. Add more navigation options (skip phases, save drafts, etc.)

---

**Quick Test Command:**
```bash
streamlit run app.py
```

Then navigate to **Project Execution** and try it out!
