#!/usr/bin/env python3
"""
Replace all 'from model import sample_data' and subsequent sample_data usage with model.sample_data
"""
import re

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Process line by line
new_lines = []
in_function = False
current_function_imports_sample_data = False
function_indent = 0

for i, line in enumerate(lines):
    # Detect function start
    stripped = line.lstrip()
    if stripped.startswith('def ') or stripped.startswith('async def '):
        in_function = True
        current_function_imports_sample_data = False
        function_indent = len(line) - len(stripped)
        new_lines.append(line)
        continue
    
    # Detect function end (dedent back to module level or another function)
    if in_function:
        if stripped and not line.startswith(' '):
            # Back to module level
            in_function = False
            current_function_imports_sample_data = False
        elif stripped.startswith('def ') or stripped.startswith('async def '):
            # New function
            current_function_imports_sample_data = False
            function_indent = len(line) - len(stripped)
    
    # Check if this line imports sample_data locally in a function
    if in_function and 'from model import' in line and 'sample_data' in line:
        # Remove this import line - we use model.sample_data instead
        print(f"Line {i+1}: Removing import: {line.strip()}")
        current_function_imports_sample_data = True
        continue  # Skip this line
    
    # Replace sample_data references with model.sample_data in function bodies
    if in_function and current_function_imports_sample_data:
        # Don't replace in comments or strings
        if not stripped.startswith('#') and 'from model import' not in line:
            # Replace word boundaries only
            modified = re.sub(r'\bsample_data\b', 'model.sample_data', line)
            modified = re.sub(r'\bdata_source\b', 'model.data_source', modified)
            modified = re.sub(r'\bANALYSIS_CACHE\b', 'model.ANALYSIS_CACHE', modified)
            
            if modified != line:
                print(f"Line {i+1}: Replaced references")
            new_lines.append(modified)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("\nDone! File updated.")
