"""
Test script to verify regex extraction works with sample data
Run this to see if our pattern matches expected format
"""

import re

# Sample orchestrator output format (assumption)
sample_output_1 = """
### File: frontend/src/App.js
```javascript
import React from 'react';

function App() {
  return <div>Hello World</div>;
}

export default App;
```

### File: backend/server.py
```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello'
```
"""

# Try our regex pattern
pattern = r'###\s*File:\s*([^\n]+)\n```[a-z]*\n(.*?)```'
matches = re.findall(pattern, sample_output_1, re.DOTALL | re.MULTILINE)

print("="*60)
print("TESTING EXTRACTION WITH SAMPLE DATA")
print("="*60)

print(f"\nSample output length: {len(sample_output_1)} characters")
print(f"Pattern: {pattern}")
print(f"\nMatches found: {len(matches)}")

if matches:
    print("\n✅ SUCCESS! Files extracted:")
    for filepath, code in matches:
        print(f"  - {filepath.strip()} ({len(code)} chars)")
else:
    print("\n❌ FAILED! No matches found.")
    print("\nTrying alternative patterns...")
    
    # Try other patterns
    alt_patterns = [
        (r'##\s*File:\s*([^\n]+)\n```[a-z]*\n(.*?)```', "Two hashes"),
        (r'File:\s*([^\n]+)\n```[a-z]*\n(.*?)```', "No hashes"),
        (r'###\s*File:\s*`([^`]+)`\n```[a-z]*\n(.*?)```', "Backticks around filename"),
    ]
    
    for alt_pattern, desc in alt_patterns:
        alt_matches = re.findall(alt_pattern, sample_output_1, re.DOTALL | re.MULTILINE)
        if alt_matches:
            print(f"  ✅ {desc}: {len(alt_matches)} matches")
        else:
            print(f"  ❌ {desc}: No matches")

print("\n" + "="*60)
print("NEXT: Check actual orchestrator output format!")
print("="*60)
print("\nIf your extraction is failing:")
print("1. Run a test build")
print("2. Look at debug output showing final_output sample")
print("3. Copy the format and test with this script")
print("4. Adjust regex pattern to match actual format")
