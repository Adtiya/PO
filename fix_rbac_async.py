#!/usr/bin/env python3
"""
Script to fix all AsyncSession compatibility issues in RBAC service.
"""

import re

def fix_rbac_async():
    """Fix all AsyncSession issues in RBAC service."""
    
    # Read the file
    with open('/home/ubuntu/enterprise_system/backend/app/services/rbac.py', 'r') as f:
        content = f.read()
    
    # Replace all session.query() patterns with async equivalents
    
    # Pattern 1: session.query(Model).filter(...).first()
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*session\.query\((\w+)\)\.filter\((.*?)\)\.first\(\)',
        r'\1\2_result = await session.execute(\n\1    select(\3).where(\4)\n\1)\n\1\2 = \2_result.scalar_one_or_none()',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Pattern 2: session.query(Model).get(id)
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*session\.query\((\w+)\)\.get\(([^)]+)\)',
        r'\1\2_result = await session.execute(\n\1    select(\3).where(\3.id == \4)\n\1)\n\1\2 = \2_result.scalar_one_or_none()',
        content,
        flags=re.MULTILINE
    )
    
    # Pattern 3: session.query(Model).options(...).filter(...).all()
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*session\.query\((\w+)\)\.options\((.*?)\)\.filter\((.*?)\)\.all\(\)',
        r'\1\2_result = await session.execute(\n\1    select(\3).options(\4).where(\5)\n\1)\n\1\2 = \2_result.scalars().all()',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Add necessary imports at the top
    if 'from sqlalchemy import select' not in content:
        # Find the import section and add the import
        import_pattern = r'(from sqlalchemy\.orm import.*?\n)'
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                r'\1from sqlalchemy import select\n',
                content,
                count=1
            )
        else:
            # Add after other sqlalchemy imports
            content = re.sub(
                r'(from sqlalchemy import.*?\n)',
                r'\1from sqlalchemy import select\n',
                content,
                count=1
            )
    
    # Write the fixed content back
    with open('/home/ubuntu/enterprise_system/backend/app/services/rbac.py', 'w') as f:
        f.write(content)
    
    print("Fixed AsyncSession issues in RBAC service")

if __name__ == "__main__":
    fix_rbac_async()

