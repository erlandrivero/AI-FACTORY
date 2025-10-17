"""
Quick diagnostic to check if our improvements executed
Run this in Streamlit app's Python environment
"""

import streamlit as st

print("\n" + "="*60)
print("DIAGNOSTIC: Checking if Improvements Activated")
print("="*60)

# Check if session state has our keys
if 'final_output' in st.session_state:
    print("✅ final_output exists in session_state")
    print(f"   Length: {len(st.session_state.final_output)} characters")
else:
    print("❌ final_output NOT in session_state (Improvement #1 failed)")

if 'original_files' in st.session_state:
    print("✅ original_files exists in session_state")
    print(f"   Files extracted: {len(st.session_state.original_files)}")
    print(f"   Files: {list(st.session_state.original_files.keys())}")
else:
    print("❌ original_files NOT in session_state (extraction failed)")

if 'files_to_fix' in st.session_state:
    print("✅ files_to_fix exists in session_state")
    print(f"   Files: {st.session_state.files_to_fix}")
else:
    print("❌ files_to_fix NOT in session_state")

if 'retry_context' in st.session_state:
    print("✅ retry_context exists in session_state")
    if "SURGICAL FIX MODE" in st.session_state.retry_context:
        print("   ✅ Contains 'SURGICAL FIX MODE'")
    else:
        print("   ❌ Does NOT contain 'SURGICAL FIX MODE'")
    
    if "ORIGINAL CODE" in st.session_state.retry_context:
        print("   ✅ Contains 'ORIGINAL CODE'")
    else:
        print("   ❌ Does NOT contain 'ORIGINAL CODE'")
else:
    print("❌ retry_context NOT in session_state")

print("="*60 + "\n")
