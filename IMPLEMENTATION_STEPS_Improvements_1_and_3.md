# 🚀 Implementation Steps for Manus's Improvements #1 & #3

## ✅ Status Check

**Completed:**
- ✅ Improvement #2: Agent profiles updated with Surgical Fix Mode

**To Implement:**
- ⏳ Improvement #1: Add original code to retry context
- ⏳ Improvement #3: Add verification and rejection loop

---

## 📋 Changes Required in `app.py`

### Change #1: Store final_output in session_state (Line ~3935)

**Location:** After line 3934 where `final_output = str(result)`

**Current Code:**
```python
# Extract and store result
if hasattr(result, 'raw'):
    final_output = str(result.raw)
elif hasattr(result, 'output'):
    final_output = str(result.output)
else:
    final_output = str(result)

# ==================================================================================
# POST-PROCESSING PHASES
```

**New Code:**
```python
# Extract and store result
if hasattr(result, 'raw'):
    final_output = str(result.raw)
elif hasattr(result, 'output'):
    final_output = str(result.output)
else:
    final_output = str(result)

# Store in session_state for retry context (needed for Improvement #1)
st.session_state.final_output = final_output

# ==================================================================================
# POST-PROCESSING PHASES
```

---

### Change #2: Add Helper Functions (Before retry context building, ~line 4200)

**Location:** Add these helper functions BEFORE the retry_context is built (around line 4150-4200)

**Add these functions:**

```python
def extract_files_from_output(output_text):
    """
    Extract individual files from the orchestrator's output.
    Looks for patterns like:
    ### File: path/to/file.ext
    ```language
    [code content]
    ```
    
    Returns dict: {filepath: code_content}
    """
    import re
    files = {}
    
    # Pattern to match: ### File: path/to/file.ext followed by code block
    # Handle both ```language and ``` formats
    pattern = r'###\s*File:\s*([^\n]+)\n```[a-z]*\n(.*?)```'
    matches = re.findall(pattern, output_text, re.DOTALL | re.MULTILINE)
    
    for filepath, code in matches:
        filepath = filepath.strip()
        files[filepath] = code.strip()
    
    return files


def extract_files_from_supervision_report(supervision_report):
    """
    Extract list of files that need fixes from Code Supervision Report.
    Looks for patterns like: **File:** `path/to/file.ext`
    
    Returns list of filepaths
    """
    import re
    file_pattern = r'\*\*File:\*\*\s*`([^`]+)`'
    files = re.findall(file_pattern, supervision_report)
    return list(set(files))  # Remove duplicates


def generate_original_code_section(original_files, files_to_fix):
    """
    Generate the 'Original Code' section for retry context.
    Only includes files that need to be fixed (from Code Supervision Report).
    """
    if not original_files or not files_to_fix:
        return ""
    
    original_code_section = "\n## 📋 ORIGINAL CODE (For Surgical Fixes)\n\n"
    original_code_section += "Below is the COMPLETE original code for each file that needs fixing.\n"
    original_code_section += "**You MUST use this as your starting point and apply ONLY the specific fixes.**\n\n"
    original_code_section += "---\n\n"
    
    for file_path in files_to_fix:
        if file_path in original_files:
            # Determine file extension for code block language
            ext = file_path.split('.')[-1] if '.' in file_path else 'text'
            language_map = {
                'py': 'python',
                'js': 'javascript',
                'jsx': 'javascript',
                'ts': 'typescript',
                'tsx': 'typescript',
                'md': 'markdown',
                'json': 'json',
                'html': 'html',
                'css': 'css'
            }
            lang = language_map.get(ext, ext)
            
            original_code_section += f"### Original Code for: `{file_path}`\n\n"
            original_code_section += f"```{lang}\n"
            original_code_section += original_files[file_path]
            original_code_section += "\n```\n\n"
            original_code_section += "---\n\n"
    
    return original_code_section
```

---

### Change #3: Modify retry_context to include original code (Lines 4223-4252)

**Location:** Where `st.session_state.retry_context` is built

**Current Code:**
```python
# Add enhanced context with supervision report for retry
st.session_state.retry_context = f"""
## 🚨🚨🚨 MANDATORY RETRY INSTRUCTIONS - READ THIS FIRST 🚨🚨🚨

### ⚠️ CRITICAL: THIS IS A RETRY - QA REJECTED PREVIOUS BUILD

**STOP AND READ**: The previous build FAILED QA validation. You are NOT building from scratch.
You are FIXING SPECIFIC ISSUES identified below. Follow these instructions EXACTLY.

---

{supervision_report if supervision_report else f'''
**Previous QA Report:**
{qa_report}

**YOU MUST FIX THESE ISSUES:**
1. **NO PLACEHOLDER COMMENTS ALLOWED**: Remove ALL comments like "// TODO", "# Implement logic here", "Replace this with..."
2. **COMPLETE ALL FUNCTIONS**: Every function must have full implementation with actual business logic
3. **USE EXTRACTED PATTERNS**: You received extracted code patterns from Phase 1 - YOU MUST USE THEM
4. **NO MOCK DATA**: No hardcoded test data or mock returns
'''}

**CRITICAL INSTRUCTIONS:**
- Fix ONLY the specific issues identified above
- DO NOT rewrite files that QA marked as passing
- PRESERVE working code - make surgical edits only
- Reference Phase 1 extracted patterns when implementing fixes
- Each fix should target the exact file and line mentioned

**THIS IS YOUR FINAL CHANCE**: If this build still has placeholder code, the system will reject it permanently.
"""
```

**New Code (with Improvement #1):**
```python
# Add enhanced context with supervision report for retry
# Extract original files for Improvement #1 (Code Context Memory)
original_files = {}
files_to_fix = []

if supervision_report and 'final_output' in st.session_state:
    original_files = extract_files_from_output(st.session_state.final_output)
    files_to_fix = extract_files_from_supervision_report(supervision_report)
    original_code_section = generate_original_code_section(original_files, files_to_fix)
else:
    original_code_section = ""

st.session_state.retry_context = f"""
## 🚨🚨🚨 MANDATORY RETRY INSTRUCTIONS - READ THIS FIRST 🚨🚨🚨

### ⚠️ CRITICAL: THIS IS A RETRY - QA REJECTED PREVIOUS BUILD

**STOP AND READ**: The previous build FAILED QA validation. You are NOT building from scratch.
You are FIXING SPECIFIC ISSUES identified below. Follow these instructions EXACTLY.

---

## 🔪 SURGICAL FIX MODE ACTIVATED

You are now in **SURGICAL FIX MODE**. This means:
- You will receive the ORIGINAL CODE for each file that needs fixing
- You must ONLY modify the lines specified in the fix instructions
- You must OUTPUT THE COMPLETE FILE with your fix incorporated
- You must NOT refactor, rewrite, or alter any other part of the file

**Failure to preserve the rest of the code is a CRITICAL ERROR.**

Your agents have been trained in Surgical Fix Mode. They know what to do.
Make sure you delegate properly to activate their surgical fix capabilities.

---

{original_code_section}

---

## 🎯 FIX INSTRUCTIONS

{supervision_report if supervision_report else f'''
**Previous QA Report:**
{qa_report}

**YOU MUST FIX THESE ISSUES:**
1. **NO PLACEHOLDER COMMENTS ALLOWED**: Remove ALL comments like "// TODO", "# Implement logic here", "Replace this with..."
2. **COMPLETE ALL FUNCTIONS**: Every function must have full implementation with actual business logic
3. **USE EXTRACTED PATTERNS**: You received extracted code patterns from Phase 1 - YOU MUST USE THEM
4. **NO MOCK DATA**: No hardcoded test data or mock returns
'''}

---

## ⚠️ CRITICAL RULES

1. **Take the ORIGINAL CODE provided above**
2. **Apply ONLY the specific fix mentioned**
3. **Output the COMPLETE file** (not just changed lines)
4. **Preserve EVERYTHING ELSE exactly as it was**

Think of yourself as a surgeon: precise incision, specific fix, preserve the rest.

**DO NOT:**
- ❌ Rewrite the entire file
- ❌ Refactor code that wasn't flagged
- ❌ Add features not requested
- ❌ Change formatting or variable names
- ❌ Fix other bugs you notice

**THIS IS YOUR FINAL CHANCE**: If you rewrite files instead of making surgical fixes, 
the system will REJECT your work.
"""

# Store original files and files_to_fix for verification (Improvement #3)
st.session_state.original_files = original_files
st.session_state.files_to_fix = files_to_fix
```

---

## 🎯 Testing After Implementing Changes #1-3

### Test Procedure:

1. **Save changes to `app.py`**
2. **Restart Streamlit app**
3. **Run a test build** (Package B recommended)
4. **Wait for QA to fail** (expected on first build)
5. **Check retry context:**
   - Should see "🔪 SURGICAL FIX MODE ACTIVATED"
   - Should see "## 📋 ORIGINAL CODE" section
   - Should see complete code for files to fix

### Expected Behavior:

✅ **Before retry:**
- QA fails with N issues
- Code Supervisor creates surgical fix instructions

✅ **Retry context includes:**
- "SURGICAL FIX MODE ACTIVATED" message
- Original code for each file to fix
- Specific fix instructions
- DO NOT rules

✅ **Agents receive:**
- Complete context with original code
- Can compare their changes to original
- Know they're in "surgical fix mode"

---

## 🚨 Note About Improvement #3 (Verification)

**Improvement #3** (verification and rejection loop) is MORE COMPLEX and requires:

1. **Intercepting agent outputs** after retry
2. **Comparing new code to original code**
3. **Detecting if changes are surgical or full rewrites**
4. **Rejecting non-compliant work**
5. **Re-running tasks with stern warnings**

This requires understanding CrewAI's execution model more deeply and may require:
- Custom callback handlers
- Task result inspection
- Dynamic re-delegation logic

**Recommendation:** 
- Implement Changes #1-3 first (Improvement #1)
- Test if providing original code alone improves results
- If whack-a-mole persists → Implement Improvement #3

---

## 📊 Expected Impact of Improvement #1 Alone

Even without Improvement #3 (verification), adding original code should help:

| Metric | Before | After Imp #1 | Improvement |
|--------|--------|--------------|-------------|
| **Agents know original** | No | Yes | 100% |
| **Agents can preserve** | Guessing | See exact code | Major |
| **Surgical fix success** | ~0% | ~30-50% | Moderate |
| **Need for verification** | Critical | Still needed | Some |

---

## 🎯 Next Steps

### Step 1: Implement Changes #1-3 (Improvement #1)
- Add helper functions
- Modify retry_context
- Store final_output in session_state

### Step 2: Test with Package B
- Run build
- Let QA fail
- Check retry context has original code
- Observe if agents preserve better

### Step 3: Evaluate Results
- If still whack-a-mole → Implement Improvement #3
- If improvement seen → Maybe sufficient
- Document findings

---

**Ready to implement? Let me know and I'll help with each code change!** 🚀
