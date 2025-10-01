#!/usr/bin/env python3
"""Fix all remaining sample_data references in app.py"""
import re

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.content()

# Track changes
changes_made = []

# Pattern 1: Replace local imports of sample_data in functions (but not at module level)
# Find pattern: "from model import sample_data" or "from model import ..., sample_data, ..."
lines = content.split('\n')
new_lines = []
inside_function = False
indent_level = 0

for i, line in enumerate(lines):
    # Track if we're inside a function
    if line.strip().startswith('def ') or line.strip().startswith('async def '):
        inside_function = True
        indent_level = len(line) - len(line.lstrip())
    elif inside_function and line.strip() and not line.startswith(' ' * (indent_level + 1)):
        inside_function = False
    
    # If inside a function and this is an import statement with sample_data
    if inside_function and 'from model import' in line and ('sample_data' in line or 'data_source' in line):
        # Remove this import line (we'll use model.sample_data instead)
        changes_made.append(f"Line {i+1}: Removed local import: {line.strip()}")
        continue
    
    # Replace sample_data with model.sample_data (but not in import statements)
    if inside_function and 'from model import' not in line:
        # Use word boundaries to avoid replacing parts of other variables
        modified_line = re.sub(r'\bsample_data\b', 'model.sample_data', line)
        modified_line = re.sub(r'\bdata_source\b', 'model.data_source', modified_line)
        
        if modified_line != line:
            changes_made.append(f"Line {i+1}: Replaced references")
        new_lines.append(modified_line)
    else:
        new_lines.append(line)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"Made {len(changes_made)} changes:")
for change in changes_made[:10]:  # Show first 10
    print(f"  {change}")
if len(changes_made) > 10:
    print(f"  ... and {len(changes_made) - 10} more")
