# Quick Test: Phases 2 & 3

## ⚡ 3-Minute Test

### Phase 2: Strategy Selection

1. **Navigate to Project Execution**
2. **Enter idea**: "Build a todo app with user authentication"
3. **Click "🎯 Plan Strategy"** - wait for Strategy Consultant
4. **Should see**: "🎯 Step 2: Choose Your Solution Package"
5. **Try this**:
   - Select "Package A" (default)
   - Or select "Package B"
   - Or select "Custom Solution" and type: "Vue.js + Firebase"
6. **Add optional config** (try it):
   - Additional Features: "Real-time sync, Push notifications"
   - Special Requirements: "Mobile responsive, PWA support"
7. **Click "Continue →"**

**✅ Expected**: Shows "✅ Selected: Package A" and moves to Phase 3

---

### Phase 3: Info Gathering

**You should see**: "🔐 Step 3: Configure API Keys & Secrets"

#### Test 1: With Netlify (Optional Keys)
If your package mentions Netlify:
- **Should see**: "Netlify API Token" field
- **Should see**: "GitHub Token" field
- **Try**: Leave them empty, click "Continue to Build →"
- **Expected**: Works! Moves to building phase with 0 keys

#### Test 2: With Supabase (Required Keys)
If your package mentions Supabase:
- **Should see**: 🔴 "Supabase URL (Required)"
- **Should see**: 🔴 "Supabase Anon Key (Required)"
- **Try**: Click "Continue to Build →" without filling
- **Expected**: Shows error "❌ Please fill in all required API keys"
- **Try**: Fill both Supabase fields with dummy values
- **Expected**: Works! Moves to building phase

#### Test 3: Skip Option
- **Click**: "⏭️ Skip & Build" button
- **Expected**: Immediately moves to building phase with message "Skipped API key configuration"

---

## 🎯 What To Look For

### Phase 2 Checklist
- [ ] Can see solution packages in expander
- [ ] Radio buttons for Package A/B/C/Custom
- [ ] Custom option shows text area
- [ ] Additional features and requirements fields work
- [ ] Back button returns to Phase 1
- [ ] Continue button moves to Phase 3
- [ ] Success message shows selected package

### Phase 3 Checklist
- [ ] Shows selected package in collapsible summary
- [ ] Dynamically shows relevant API key fields
- [ ] Required keys marked with 🔴
- [ ] Optional keys marked with ⚪
- [ ] All inputs are password-masked
- [ ] Help text shows where to get each key
- [ ] Can't submit without required keys
- [ ] Can submit with only required keys filled
- [ ] Skip button works
- [ ] Back button returns to Phase 2
- [ ] Success message shows number of keys configured

---

## 🔍 Debug: Check Session State

Add this code temporarily to see what's stored:

```python
with st.expander("🐛 Debug Info"):
    st.write("**Phase:**", st.session_state.phase)
    st.write("**Chosen Strategy:**", st.session_state.chosen_strategy)
    st.write("**User Selections:**", st.session_state.user_selections)
    st.write("**API Keys:**", len(st.session_state.get('api_keys', {})), "configured")
```

---

## 📋 Expected API Keys by Stack

### Package with Netlify
- ⚪ Netlify API Token
- ⚪ GitHub Token

### Package with Vercel
- ⚪ Vercel Token
- ⚪ GitHub Token

### Package with Supabase
- 🔴 Supabase URL (required!)
- 🔴 Supabase Anon Key (required!)
- ⚪ GitHub Token

### Package with Firebase
- 🔴 Firebase Config (required!)
- ⚪ GitHub Token

### Package with OpenAI/GPT
- ⚪ OpenAI API Key
- ⚪ GitHub Token

### Package with Stripe
- ⚪ Stripe API Key
- ⚪ Stripe Webhook Secret
- ⚪ GitHub Token

---

## 🎬 Full Workflow Demo

```
1. Phase 1: idea_input
   ↓ Enter: "Build a recipe sharing app"
   ↓ Click: "🎯 Plan Strategy"
   ↓ Wait: Strategy Consultant analyzes...
   
2. Phase 2: strategy_selection
   ✓ See: 3 solution packages
   ↓ Select: "Package B"
   ↓ Type: Additional Features = "Comments, Ratings"
   ↓ Click: "Continue →"
   
3. Phase 3: info_gathering
   ✓ See: Relevant API key fields
   ↓ Option A: Fill keys and click "Continue to Build →"
   ↓ Option B: Click "⏭️ Skip & Build"
   
4. Phase 4: building
   ✓ Existing logic runs with chosen package and API keys
   
5. Phase 5: complete
   ✓ Results displayed
```

---

## ❌ Common Issues

### "No API keys detected"
- Package name doesn't contain recognizable keywords
- Try "Custom Solution" with explicit tech names

### "Can't continue from Phase 2"
- Make sure you selected a package
- Check console for errors

### "Form won't submit in Phase 3"
- Required keys (🔴) must be filled
- Or use "⏭️ Skip & Build" to bypass

### "Back button doesn't work"
- Use the in-form "← Back" button, not browser back

---

## ✅ Success Indicators

You know it works when:

✓ **Phase 2**: Selected package saved to `st.session_state.chosen_strategy`  
✓ **Phase 3**: Correct API keys appear based on package  
✓ **Phase 3**: Required validation works  
✓ **Phase 3**: Skip option works  
✓ **Navigation**: Can go back and forth between phases  
✓ **Storage**: All data persists in session state  

---

## 🚀 Ready to Test?

```bash
streamlit run app.py
```

1. Go to **Project Execution**
2. You'll see phase progress at top
3. Follow the workflow from Phase 1 → 2 → 3
4. Try different packages and options
5. Check that keys are detected correctly

---

**Quick Tip:** Use "Custom Solution" to test specific API key detection:
- Type "Supabase" → see required Supabase keys
- Type "Netlify" → see optional Netlify token
- Type "OpenAI" → see optional OpenAI key
- Type "Stripe" → see Stripe keys

Have fun testing! 🎉
