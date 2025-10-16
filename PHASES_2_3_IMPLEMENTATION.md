# Phase 2 & 3 Implementation Guide

## ✅ What Was Implemented

### Phase 2: Strategy Selection
### Phase 3: Info Gathering

---

## 📋 Phase 2: Strategy Selection (Lines 1490-1568)

### Purpose
Allow users to select one of the solution packages presented by the Strategy Consultant.

### Features Implemented

#### 1. **Display Strategy Options**
```python
with st.expander("📦 Solution Packages Analysis", expanded=True):
    st.markdown(st.session_state.strategy_options)
```
- Shows the complete Strategy Consultant output
- Expanded by default for easy review
- User can collapse if needed

#### 2. **Package Selection UI**
```python
package_choice = st.radio(
    "Which solution package would you like to use?",
    options=["Package A", "Package B", "Package C", "Custom Solution"],
    index=0,
    key="package_selection_radio"
)
```
- Radio buttons for clear single-choice selection
- 4 options: Package A, B, C, or Custom
- Default selection is Package A

#### 3. **Custom Solution Option**
```python
if package_choice == "Custom Solution":
    custom_details = st.text_area(
        "Describe your custom solution",
        placeholder="e.g., Next.js + Supabase + Vercel...",
        key="custom_solution_input"
    )
    if custom_details:
        package_choice = f"Custom: {custom_details}"
```
- If user selects "Custom Solution"
- Text area appears for custom stack description
- Final choice becomes "Custom: [user description]"

#### 4. **Additional Configuration**
```python
additional_features = st.text_area("Additional Features (Optional)", ...)
special_requirements = st.text_area("Special Requirements (Optional)", ...)
```
- Two text areas for extra requirements
- Features: Real-time updates, notifications, analytics, etc.
- Requirements: GDPR, mobile-first, offline support, etc.

#### 5. **State Management**
```python
st.session_state.chosen_strategy = package_choice
st.session_state.user_selections = {
    'package': package_choice,
    'additional_features': additional_features,
    'special_requirements': special_requirements
}
```
- Stores selected package in `chosen_strategy`
- Stores all selections in `user_selections` dict
- Persists across page interactions

#### 6. **Navigation**
- **Back Button**: Returns to `'idea_input'` phase
- **Continue Button**: Moves to `'info_gathering'` phase
- Shows success message with selected package

---

## 🔐 Phase 3: Info Gathering (Lines 1573-1713)

### Purpose
Collect API keys and secrets based on the chosen technology stack.

### Features Implemented

#### 1. **Dynamic API Key Detection**

The system automatically detects which API keys are needed based on:
- **Chosen strategy** (`st.session_state.chosen_strategy`)
- **Strategy options text** (`st.session_state.strategy_options`)

##### Detection Logic Examples:

**Deployment Platforms:**
```python
if "netlify" in chosen_strategy_lower:
    optional_keys["Netlify API Token"] = "Get from: app.netlify.com..."
if "vercel" in chosen_strategy_lower:
    optional_keys["Vercel Token"] = "Get from: vercel.com/account/tokens"
if "railway" in chosen_strategy_lower:
    optional_keys["Railway Token"] = "Get from: railway.app/account/tokens"
```

**Databases:**
```python
if "supabase" in chosen_strategy_lower:
    required_keys["Supabase URL"] = "Your Supabase project URL"
    required_keys["Supabase Anon Key"] = "Your Supabase anon/public key"
if "firebase" in chosen_strategy_lower:
    required_keys["Firebase Config"] = "Your Firebase configuration object"
if "postgres" in chosen_strategy_lower:
    optional_keys["Database URL"] = "PostgreSQL connection string"
```

**Services:**
```python
if "openai" in chosen_strategy_lower or "gpt" in chosen_strategy_lower:
    optional_keys["OpenAI API Key"] = "Get from: platform.openai.com/api-keys"
if "stripe" in chosen_strategy_lower:
    optional_keys["Stripe API Key"] = "Get from: dashboard.stripe.com/apikeys"
```

**Always Included:**
```python
optional_keys["GitHub Token"] = "For automated deployment and CI/CD"
```

#### 2. **Required vs Optional Keys**

**Required Keys** (🔴):
- Must be filled to continue
- Validation prevents submission without them
- Currently: Supabase URL/Key, Firebase Config

**Optional Keys** (⚪):
- Can be left empty
- Useful but not blocking
- Most deployment and service keys

#### 3. **Form Implementation**

```python
with st.form("api_keys_form", clear_on_submit=False):
    # Required keys section
    st.markdown("### 🔑 Required API Keys")
    if required_keys:
        required_values = {}
        for key_name, key_help in required_keys.items():
            required_values[key_name] = st.text_input(
                f"🔴 {key_name} (Required)",
                type="password",  # Masked input
                help=key_help,
                key=f"required_{key_name.replace(' ', '_').lower()}"
            )
    
    # Optional keys section
    st.markdown("### 🔓 Optional API Keys")
    if optional_keys:
        optional_values = {}
        for key_name, key_help in optional_keys.items():
            optional_values[key_name] = st.text_input(
                f"⚪ {key_name} (Optional)",
                type="password",  # Masked input
                help=key_help,
                key=f"optional_{key_name.replace(' ', '_').lower()}"
            )
```

**Features:**
- All inputs use `type="password"` for security
- Each input has helpful text showing where to get the key
- Dynamic keys based on selected stack
- Form prevents duplicate submissions

#### 4. **Validation**

```python
if submit_button:
    # Validate required keys
    if required_keys:
        all_required_filled = all(required_values.get(k, "").strip() for k in required_keys.keys())
        if not all_required_filled:
            st.error("❌ Please fill in all required API keys before continuing.")
            st.stop()
```

- Checks all required keys are filled
- Shows error and stops if validation fails
- Only validates required keys, not optional

#### 5. **Storage**

```python
# Store all API keys
api_keys = {}

if required_keys:
    for key_name, value in required_values.items():
        if value.strip():
            api_keys[key_name] = value.strip()

if optional_keys:
    for key_name, value in optional_values.items():
        if value.strip():
            api_keys[key_name] = value.strip()

st.session_state.api_keys = api_keys
```

- Stores all non-empty keys in `st.session_state.api_keys`
- Strips whitespace from values
- Skips empty optional keys

#### 6. **Navigation Options**

**Inside Form:**
- **← Back**: Returns to `'strategy_selection'` phase
- **Continue to Build →**: Validates and moves to `'building'` phase

**Outside Form:**
- **⏭️ Skip & Build**: Bypasses API key collection entirely
  - Sets `api_keys` to empty dict
  - Moves to `'building'` phase immediately

#### 7. **User Feedback**

```python
st.info("💡 **Tip:** You can skip this step and add API keys later during deployment.")
```

Success messages:
```python
st.success(f"✅ Configured {len(api_keys)} API key(s). Proceeding to build...")
st.info("Skipped API key configuration. You can add them during deployment.")
```

---

## 🔄 Complete Workflow Flow

```
Phase 1: idea_input
    ↓ (Click "🎯 Plan Strategy")
    ↓ [Strategy Consultant runs]
    ↓
Phase 2: strategy_selection
    ↓ (Select package)
    ↓ (Click "Continue →")
    ↓
Phase 3: info_gathering
    ↓ (Fill API keys OR skip)
    ↓ (Click "Continue to Build →" OR "⏭️ Skip & Build")
    ↓
Phase 4: building
    ↓ (Crew builds project)
    ↓
Phase 5: complete
    ↓ (Show results)
```

---

## 📊 Session State Variables

### New Variables Added

```python
# Phase 2
st.session_state.chosen_strategy = "Package A"  # Selected package

st.session_state.user_selections = {
    'package': 'Package A',
    'additional_features': '...',
    'special_requirements': '...'
}

# Phase 3
st.session_state.api_keys = {
    'Netlify API Token': 'xxxxx',
    'GitHub Token': 'ghp_xxxxx',
    'OpenAI API Key': 'sk-xxxxx'
}
```

### Existing Variables Used

```python
st.session_state.phase = 'info_gathering'  # Current phase
st.session_state.strategy_options = "..."  # Strategy Consultant output
st.session_state.project_idea = "..."     # User's project description
```

---

## 🧪 Testing Guide

### Test Phase 2: Strategy Selection

1. **Start from phase 1**, enter an idea, get strategy
2. **Verify display**: Solution packages show in expander
3. **Test Package A**: Select and continue
4. **Test Package B**: Select and continue
5. **Test Package C**: Select and continue
6. **Test Custom**: Select "Custom Solution", enter details
7. **Test additional fields**: Add features and requirements
8. **Test navigation**: Back button returns to idea_input
9. **Verify storage**: Check `st.session_state.chosen_strategy`

### Test Phase 3: Info Gathering

#### Test Scenario 1: Netlify Stack
```
Chosen strategy: "Package A: Next.js + Netlify"
Expected keys: Netlify API Token, GitHub Token
```

1. Select package mentioning Netlify
2. Verify "Netlify API Token" appears
3. Try continuing without filling required keys (should fail)
4. Fill required keys and continue
5. Verify `st.session_state.api_keys` contains entered values

#### Test Scenario 2: Supabase Stack
```
Chosen strategy: "Package B: React + Supabase + Vercel"
Expected keys: Supabase URL (required), Supabase Anon Key (required), Vercel Token, GitHub Token
```

1. Select package mentioning Supabase
2. Verify required keys marked with 🔴
3. Try continuing without filling (should show error)
4. Fill only Supabase keys, leave others empty
5. Should succeed and move to building

#### Test Scenario 3: Skip Option
```
Any package selected
```

1. Navigate to info_gathering phase
2. Don't fill any keys
3. Click "⏭️ Skip & Build"
4. Should move to building phase
5. Verify `st.session_state.api_keys` is empty dict

#### Test Scenario 4: Back Navigation
```
Any package selected
```

1. Navigate to info_gathering phase
2. Fill some keys
3. Click "← Back" button in form
4. Should return to strategy_selection
5. Verify keys are NOT saved yet

---

## 🎨 UI/UX Highlights

### Strategy Selection Phase
- ✅ Clean radio button selection
- ✅ Custom solution text area appears conditionally
- ✅ Two-column layout for additional config
- ✅ Clear navigation buttons
- ✅ Success message on selection

### Info Gathering Phase
- ✅ Shows selected package summary in collapsible section
- ✅ Dynamic key detection based on stack
- ✅ Visual distinction: 🔴 Required vs ⚪ Optional
- ✅ Password-masked inputs for security
- ✅ Helpful text for where to get each key
- ✅ Multiple exit options (back, submit, skip)
- ✅ Validation with clear error messages
- ✅ Success message showing count of configured keys

---

## 🔑 API Key Detection Matrix

| Technology | Detection String | Key Type | Key Name |
|-----------|------------------|----------|----------|
| Netlify | "netlify" | Optional | Netlify API Token |
| Vercel | "vercel" | Optional | Vercel Token |
| Railway | "railway" | Optional | Railway Token |
| Render | "render" | Optional | Render API Key |
| Heroku | "heroku" | Optional | Heroku API Key |
| Supabase | "supabase" | Required | Supabase URL, Supabase Anon Key |
| Firebase | "firebase" | Required | Firebase Config |
| MongoDB Atlas | "mongodb" + "atlas" | Optional | MongoDB Atlas URI |
| PostgreSQL | "postgres" | Optional | Database URL |
| OpenAI | "openai" or "gpt" | Optional | OpenAI API Key |
| Stripe | "stripe" | Optional | Stripe API Key, Stripe Webhook Secret |
| SendGrid | "sendgrid" or "email" | Optional | SendGrid API Key |
| Twilio | "twilio" | Optional | Twilio Account SID, Twilio Auth Token |
| GitHub | Always | Optional | GitHub Token |

---

## ⚠️ Important Notes

1. **Case-Insensitive Detection**: All detection uses `.lower()` for reliability

2. **Two Sources**: Checks both `chosen_strategy` AND `strategy_options` for keywords

3. **Security**: All API key inputs use `type="password"` - values are masked

4. **Flexibility**: Users can skip API key collection entirely

5. **Validation**: Only required keys block progression

6. **Storage**: Keys stored in session state, passed to building phase

7. **Form Keys**: Each input has unique key to prevent conflicts

---

## 🚀 Next Steps

With Phases 2 and 3 complete, the workflow is:

✅ Phase 1: idea_input (DONE)  
✅ Phase 2: strategy_selection (DONE)  
✅ Phase 3: info_gathering (DONE)  
⏳ Phase 4: building (existing logic)  
⏳ Phase 5: complete (existing logic)  

**To fully integrate:**
- Phase 4 should use `st.session_state.chosen_strategy` in task descriptions
- Phase 4 should include `st.session_state.api_keys` in generated code/docs
- Phase 5 should display selected package and configured keys in results

---

## 🐛 Troubleshooting

### Issue: No API keys detected
**Solution**: Make sure package name contains recognizable keywords (netlify, vercel, supabase, etc.)

### Issue: Form doesn't submit
**Solution**: Check if required keys are filled. Error message should appear.

### Issue: Can't go back
**Solution**: Use the "← Back" button inside the form, not browser back button

### Issue: Keys not saved after skip
**Solution**: This is expected - skipping sets `api_keys` to empty dict

### Issue: Wrong keys detected
**Solution**: Detection is based on keywords in package name. Be specific in package selection or custom description.

---

**Implementation Date:** October 15, 2025  
**Phases Completed:** 2 (strategy_selection), 3 (info_gathering)  
**Lines Added:** ~240 lines  
**Files Modified:** `app.py`
