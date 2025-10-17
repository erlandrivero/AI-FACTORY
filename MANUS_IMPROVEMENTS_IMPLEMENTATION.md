# 🚀 Manus's Three Improvements - Implementation Guide

## Overview

These three improvements work together to solve the "whack-a-mole" problem by:
1. **Giving agents memory** (original code context)
2. **Teaching agents two modes** (creation vs surgical fix)
3. **Enforcing compliance** (verification and rejection)

---

## ✅ Improvement #1: Code Context Memory Upgrade

### What It Does
When retrying, the Orchestrator includes the **complete original file code** in the task prompt, so Coder agents can see what they're fixing.

### Where to Implement
**File:** `app.py`  
**Function:** Around line 4220-4250 (where `retry_context` is built)

### Current Code Structure:
```python
st.session_state.retry_context = f"""
## 🚨🚨🚨 MANDATORY RETRY INSTRUCTIONS
{supervision_report}
"""
```

### New Code Structure:
```python
# STEP 1: Extract original code from final_output
# We need to parse final_output to get each file's code

def extract_files_from_output(final_output):
    """Extract individual files from the orchestrator's output"""
    files = {}
    import re
    
    # Pattern to match: ### File: path/to/file.ext
    # followed by code block
    pattern = r'###\s*File:\s*([^\n]+)\n```[a-z]*\n(.*?)```'
    matches = re.findall(pattern, final_output, re.DOTALL)
    
    for filepath, code in matches:
        files[filepath.strip()] = code.strip()
    
    return files

# STEP 2: Build retry context with original code
if supervision_report and st.session_state.get('final_output'):
    original_files = extract_files_from_output(st.session_state.final_output)
    
    # Parse supervision report to get which files need fixes
    # (You'll need to parse the supervision_report to extract file paths)
    
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

---

## 📋 ORIGINAL CODE

{generate_original_code_section(original_files, supervision_report)}

---

## 🎯 FIX INSTRUCTIONS

{supervision_report}

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
```

### Helper Function to Add:
```python
def generate_original_code_section(original_files, supervision_report):
    """
    Generate the 'Original Code' section for retry context.
    Only include files that need to be fixed.
    """
    # Parse supervision report to extract which files need fixes
    import re
    
    # Extract file paths from supervision report
    # Pattern: **File:** `path/to/file.ext`
    file_pattern = r'\*\*File:\*\*\s*`([^`]+)`'
    files_to_fix = re.findall(file_pattern, supervision_report)
    
    original_code_section = ""
    
    for file_path in files_to_fix:
        if file_path in original_files:
            original_code_section += f"""
### Original Code for: `{file_path}`

```
{original_files[file_path]}
```

---

"""
    
    return original_code_section
```

### What This Achieves:
- ✅ Agents see the complete original file
- ✅ Agents can compare their output to original
- ✅ Agents understand what "preserve the rest" means
- ✅ Prevents "I forgot what was there before" problem

---

## ✅ Improvement #2: Surgical Coder Agent Profile Upgrade

### What It Does
Updates Coder agent profiles to explicitly teach them about "Creation Mode" vs "Surgical Fix Mode".

### Where to Implement
**Location:** Agent Management UI (MongoDB)  
**Agents to Update:**
1. Backend Developer
2. Frontend Developer

### Implementation Steps:

#### Step 1: Update Backend Developer
1. Go to Agent Management
2. Find agent with "Backend" in role name
3. Click Edit
4. Replace **Backstory** field with content from `SURGICAL_CODER_PROFILES.md` (Backend Developer section)
5. Save

#### Step 2: Update Frontend Developer
1. Go to Agent Management
2. Find agent with "Frontend" in role name
3. Click Edit
4. Replace **Backstory** field with content from `SURGICAL_CODER_PROFILES.md` (Frontend Developer section)
5. Save

### Key Phrases in New Profiles:
- "surgical fix mode" (detection trigger)
- "Original Code" (what to look for in task)
- "ONLY job is to apply the specific changes"
- "Failure to preserve the rest of the code is a critical error"

### What This Achieves:
- ✅ Agents have explicit mental model for two modes
- ✅ Agents know to look for "Original Code" in task
- ✅ Agents understand preservation is mandatory
- ✅ Reduces "eager refactorer" problem

---

## ✅ Improvement #3: Verification & Rejection Orchestrator Upgrade

### What It Does
After a Coder finishes a surgical fix, the Orchestrator verifies the fix was surgical (not a rewrite) before sending to QA.

### Where to Implement
**File:** `app.py`  
**Location:** After orchestrator execution during retry (around line 3800-3850)

### Conceptual Flow:
```
Retry Mode:
1. Orchestrator delegates fix tasks to Coders
2. Coders return "fixed" code
3. ⭐ NEW: Verification Step
   - Compare new code to original code
   - Check if changes are localized
   - Decision: Accept or Reject
4a. If Accept → Send to QA
4b. If Reject → Re-run task with stern warning
```

### Implementation Code:

```python
def verify_surgical_fix(original_code, new_code, fix_instructions):
    """
    Verify that the new code only contains surgical changes.
    Returns: (is_surgical: bool, reason: str)
    """
    # Simple heuristics to detect full rewrites:
    
    # 1. Length Check: New code shouldn't be drastically different in length
    orig_lines = original_code.split('\n')
    new_lines = new_code.split('\n')
    
    length_diff_ratio = abs(len(new_lines) - len(orig_lines)) / len(orig_lines)
    
    if length_diff_ratio > 0.3:  # More than 30% length change
        return False, f"File length changed by {length_diff_ratio*100:.0f}% (expected <30% for surgical fix)"
    
    # 2. Major Section Preservation: Check if large unchanged sections exist
    # Use difflib to find unchanged blocks
    import difflib
    
    matcher = difflib.SequenceMatcher(None, orig_lines, new_lines)
    
    # Find longest unchanged block
    longest_match = max(matcher.get_matching_blocks(), key=lambda x: x.size)
    
    if longest_match.size < len(orig_lines) * 0.5:  # Less than 50% of file unchanged
        return False, "Less than 50% of original code preserved (expected >50% for surgical fix)"
    
    # 3. Check if changes are localized (not scattered throughout)
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            changes.append((i1, i2))
    
    if len(changes) > 3:  # More than 3 separate change blocks
        return False, f"Changes scattered across {len(changes)} locations (expected 1-3 for surgical fix)"
    
    # If all checks pass
    return True, "Surgical fix verified: localized changes, majority of code preserved"


def execute_retry_with_verification(orchestrator_agent, retry_task, original_files, supervision_report, max_rejection_attempts=2):
    """
    Execute retry with verification and rejection loop.
    """
    rejection_count = 0
    retry_warning = ""
    
    while rejection_count <= max_rejection_attempts:
        # Build task description with retry context + warning if rejected before
        task_description = f"""
{st.session_state.retry_context}

{retry_warning}

Now execute the surgical fixes.
"""
        
        # Create task
        retry_task = Task(
            description=task_description,
            expected_output="Complete updated source code files with surgical fixes applied",
            agent=orchestrator_agent
        )
        
        # Execute
        crew = Crew(
            agents=[orchestrator_agent],
            tasks=[retry_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        new_output = str(result)
        
        # Extract new files from output
        new_files = extract_files_from_output(new_output)
        
        # Verify each fixed file
        verification_passed = True
        verification_failures = []
        
        # Parse supervision report to get which files should be fixed
        files_to_verify = extract_files_from_supervision_report(supervision_report)
        
        for file_path in files_to_verify:
            if file_path in original_files and file_path in new_files:
                is_surgical, reason = verify_surgical_fix(
                    original_files[file_path],
                    new_files[file_path],
                    supervision_report
                )
                
                if not is_surgical:
                    verification_passed = False
                    verification_failures.append(f"- {file_path}: {reason}")
        
        # Decision Gate
        if verification_passed:
            st.success("✅ Verification Passed: Surgical fixes confirmed")
            return new_output, True
        else:
            # REJECT
            rejection_count += 1
            st.warning(f"❌ Verification Failed (Attempt {rejection_count}/{max_rejection_attempts})")
            st.write("**Rejection Reasons:**")
            for failure in verification_failures:
                st.write(failure)
            
            if rejection_count <= max_rejection_attempts:
                # Build stern warning for next attempt
                retry_warning = f"""
## 🚨 ATTENTION: YOUR PREVIOUS SUBMISSION WAS REJECTED 🚨

**Rejection Count:** {rejection_count} of {max_rejection_attempts}

**Why Your Work Was Rejected:**
{chr(10).join(verification_failures)}

**What Went Wrong:**
You REWROTE the entire file instead of applying the surgical fix. This is a CRITICAL ERROR.

**What You MUST Do Differently:**
1. COPY the ENTIRE "Original Code" provided
2. FIND the specific line mentioned in fix instructions  
3. CHANGE only that line
4. OUTPUT the complete file with ONLY that one change

**Think:** If the original file has 100 lines, and you're fixing line 50, 
your output should have ~100 lines, with 99 lines identical to original.

**This is your {"final" if rejection_count == max_rejection_attempts else "next"} chance.** 
Follow the instructions PRECISELY or your work will be permanently rejected.
"""
                
                st.info(f"⏳ Re-running task with stern warning (Attempt {rejection_count + 1})...")
                time.sleep(2)
            else:
                # Max rejections reached
                st.error(f"❌ Max rejections ({max_rejection_attempts}) reached. Using last attempt despite failures.")
                return new_output, False
    
    return None, False


def extract_files_from_supervision_report(supervision_report):
    """Extract list of files that need fixes from supervision report"""
    import re
    file_pattern = r'\*\*File:\*\*\s*`([^`]+)`'
    return re.findall(file_pattern, supervision_report)
```

### Integration Point in `app.py`:

Find where retry happens (around line 4254):
```python
st.info("⏳ Restarting build with targeted fix instructions...")
time.sleep(2)
st.rerun()
```

Replace with:
```python
st.info("⏳ Executing retry with verification and rejection loop...")

# Get original files from previous build
if 'final_output' in st.session_state:
    original_files = extract_files_from_output(st.session_state.final_output)
    
    # Execute retry with verification
    verified_output, verification_passed = execute_retry_with_verification(
        orchestrator_agent=orchestrator_profile,  # Need to get this from saved_agents
        retry_task=None,  # Will be created in function
        original_files=original_files,
        supervision_report=supervision_report,
        max_rejection_attempts=2
    )
    
    if verified_output:
        # Update final_output with verified fixes
        st.session_state.final_output = verified_output
        st.session_state.retry_attempts += 1
        
        # Re-run QA on verified output
        st.info("⏳ Re-running QA validation on verified fixes...")
        time.sleep(1)
        st.rerun()
    else:
        st.error("❌ Retry failed verification. Proceeding with last attempt.")
else:
    st.error("❌ Original code not found. Cannot perform verification.")
    st.info("⏳ Restarting build without verification...")
    time.sleep(2)
    st.rerun()
```

### What This Achieves:
- ✅ Catches full rewrites before QA sees them
- ✅ Gives agents immediate feedback on non-compliance
- ✅ Stern warning escalates with each rejection
- ✅ Prevents whack-a-mole from reaching QA

---

## 🔄 Complete New Workflow

### Before Manus's Improvements:
```
1. Initial Build → Has 3 issues
2. QA Fails
3. Code Supervisor creates fix instructions
4. Retry: Orchestrator says "fix these issues"
5. Coders rebuild everything
6. QA Fails with different issues (whack-a-mole)
```

### After Manus's Improvements:
```
1. Initial Build → Has 3 issues
2. QA Fails
3. Code Supervisor creates fix instructions
4. Retry Context Built:
   ✨ Includes ORIGINAL CODE for each file
   ✨ Includes "🔪 SURGICAL FIX MODE ACTIVATED"
5. Orchestrator delegates with original code
6. Coders (with new profiles):
   ✨ Recognize "surgical fix mode"
   ✨ Load original code
   ✨ Apply only specified fixes
   ✨ Output complete file with fix
7. ✨ NEW: Verification Step
   - Compare new vs original
   - Check if changes are surgical
   - If NO: Reject with stern warning, retry
   - If YES: Proceed to QA
8. QA validates verified fixes
9. Success: Only specified issues fixed, rest preserved
```

---

## 📊 Expected Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Whack-a-Mole** | 100% (always happens) | <10% (rare) | 90% reduction |
| **Preserved Files Violated** | Often | Rarely | Major improvement |
| **Retry Success Rate** | ~0% | ~80% | Massive improvement |
| **Quality Progression** | 6→5→6 (circle) | 6→3→0 (progress) | Progressive fixes |
| **Build Time** | 3x longer (retries fail) | 1.5x (retries work) | 50% time saved |

---

## 🚀 Implementation Priority

### Phase 1: Quick Win (5 minutes)
✅ **Improvement #2**: Update agent profiles  
- No code changes required
- Immediate impact
- Teaches agents two modes

### Phase 2: Foundation (30 minutes)
✅ **Improvement #1**: Add original code to retry context  
- Modify `app.py` lines 4220-4250
- Add helper functions
- Gives agents memory

### Phase 3: Enforcement (1 hour)
✅ **Improvement #3**: Add verification and rejection  
- Modify `app.py` around line 4254
- Add verification functions
- Enforces compliance

---

## 🧪 Testing the Improvements

After implementing all three:

### Test Scenario:
1. Build data cleaning app (Package B)
2. QA fails with 3 issues
3. **Watch for:**
   - ✅ Retry context includes "🔪 SURGICAL FIX MODE ACTIVATED"
   - ✅ Retry context includes "Original Code" sections
   - ✅ Verification step runs after retry
   - ✅ If verification fails, rejection warning appears
   - ✅ Final QA shows only specified issues fixed

### Success Criteria:
- **No whack-a-mole:** New issues in different files
- **Preserved files untouched:** Files marked preserved stay unchanged
- **Progressive improvement:** 6→3→0, not 6→5→6

---

## 📝 Next Steps

1. **Immediately:** Update agent profiles (#2) ← 5 minutes
2. **Today:** Implement code context memory (#1) ← 30 minutes
3. **Tomorrow:** Add verification and rejection (#3) ← 1 hour
4. **Test:** Run full test with all three improvements
5. **Celebrate:** When whack-a-mole is finally defeated! 🎉

---

**These improvements transform the system from a "rebuild everything" pipeline to a true "surgical fix" system.**
