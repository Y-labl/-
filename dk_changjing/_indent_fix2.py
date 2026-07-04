# -*- coding: utf-8 -*-
"""Proper indentation fixer using an indent stack."""

path = r'D:\Program Files\mhxy-project\dk_changjing\core\original\game_action\map_action.py'

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Strategy: for lines inside a def/if/for/while/else/try/except block,
# the decompiler put them at the SAME level as the block starter's NEXT indent.
# We need to add 4 spaces for each nesting level.
# 
# Algorithm: track a stack of indent levels.
# - def/if/for/while/try/except/else/elif line ending with ':' -> push stack
# - elif/else/except: pop then push at same level
# - Everything else: should be at current stack top

result = []
# Don't run on the whole file - just fix lines from getMapParams onwards
# where the v2 decompiler had flat blocks
start_fixing_from = None
for i, line in enumerate(lines):
    if 'def getMapParams' in line:
        start_fixing_from = i
        break

if start_fixing_from is None:
    print('ERROR: getMapParams not found')
    exit(1)

# Copy lines before getMapParams as-is  
for i in range(start_fixing_from):
    result.append(lines[i])

# Now fix from getMapParams onwards
indent_stack = [4]  # def body starts at 4 spaces

for i in range(start_fixing_from, len(lines)):
    line = lines[i]
    stripped = line.rstrip()
    
    if not stripped:
        result.append('\n')
        continue
    
    # Get current content and leading spaces  
    leading = len(line) - len(line.lstrip(' '))
    content = line.lstrip(' ')
    
    # Determine line type
    is_def = content.startswith('def ')
    is_if = content.startswith('if ')
    is_for = content.startswith('for ')
    is_while = content.startswith('while ')
    is_else = content.startswith('else:')
    is_elif = content.startswith('elif ')
    is_except = content.startswith('except')
    is_finally = content.startswith('finally:')
    is_try = content.startswith('try:')
    is_return = content.startswith('return ')
    is_pass = content.startswith('pass ')
    is_block_end = is_else or is_elif or is_except or is_finally
    is_block_start = (is_if or is_for or is_while or is_try or is_def) and not is_block_end
    
    # Compute expected indent
    if is_def:
        # def resets stack
        indent_stack = [0, 4]
        expected = 0
    elif is_block_end:
        # pop back to parent level
        if len(indent_stack) >= 2:
            indent_stack.pop()
        expected = indent_stack[-1] if indent_stack else 0
    else:
        expected = indent_stack[-1] if indent_stack else 0
    
    # Apply indent
    new_line = ' ' * expected + content + '\n'
    result.append(new_line)
    
    # Update stack for next line
    if is_block_start:
        indent_stack.append(expected + 4)
    elif is_block_end:
        indent_stack.append(expected + 4)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(result)

print(f'Fixed {len(lines) - start_fixing_from} lines from getMapParams onwards')