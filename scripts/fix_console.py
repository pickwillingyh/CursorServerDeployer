#!/usr/bin/env python3
"""
Fix console.print calls to handle None console
"""

import re
from pathlib import Path

# Read the file
file_path = Path("src/cursor_server_deployer/download/manager.py")
content = file_path.read_text()

# Replace self.console.print with if self.console: check
# This is a complex regex to handle indentation properly
pattern = r'(^[ \t]*)self\.console\.print\((.*?)\)([ \t]*)$'

def replace_console(match):
    indent = match.group(1)
    code = match.group(2)
    suffix = match.group(3)

    # Preserve newlines in the code
    if '\n' in code:
        # Multi-line case - more complex handling
        lines = code.split('\n')
        result = f"{indent}if self.console:\n{indent}    self.console.print(\n"
        for line in lines[1:]:
            result += f"{indent}    {line}\n"
        result = result.rstrip()
        result += f"{suffix})"
        return result
    else:
        # Single line case
        return f'{indent}if self.console:\n{indent}    self.console.print({code}){suffix}'

# Apply the replacement
content = re.sub(pattern, replace_console, content, flags=re.MULTILINE)

# Write back
file_path.write_text(content)
print("Fixed console.print calls")