#!/usr/bin/env python3
"""
Script to fix all AsyncSession compatibility issues in permissions endpoint.
"""

import re

def fix_permissions_async():
    """Fix all AsyncSession issues in permissions endpoint."""
    
    # Read the file
    with open('/home/ubuntu/enterprise_system/backend/app/api/v1/endpoints/permissions.py', 'r') as f:
        content = f.read()
    
    # Add select import if not present
    if 'from sqlalchemy import select' not in content:
        content = re.sub(
            r'(from sqlalchemy import.*?\n)',
            r'\1from sqlalchemy import select\n',
            content,
            count=1
        )
    
    # Replace session.query(Model).filter(...).first() patterns
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*session\.query\((\w+)\)\.filter\((.*?)\)\.first\(\)',
        r'\1\2_result = await session.execute(\n\1    select(\3).where(\4)\n\1)\n\1\2 = \2_result.scalar_one_or_none()',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Replace session.query(Model).filter(...).all() patterns
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*session\.query\((\w+)\)\.filter\((.*?)\)\.all\(\)',
        r'\1\2_result = await session.execute(\n\1    select(\3).where(\4)\n\1)\n\1\2 = \2_result.scalars().all()',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Replace session.query(Model).filter(...).options(...).all() patterns
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*session\.query\((\w+)\)\.options\((.*?)\)\.filter\((.*?)\)\.all\(\)',
        r'\1\2_result = await session.execute(\n\1    select(\3).options(\4).where(\5)\n\1)\n\1\2 = \2_result.scalars().all()',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Replace session.query(...).distinct() patterns
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*session\.query\((.*?)\)\.distinct\(\)',
        r'\1\2_result = await session.execute(\n\1    select(\3).distinct()\n\1)\n\1\2 = \2_result.scalars().all()',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Replace session.query(...).filter(...).delete() patterns
    content = re.sub(
        r'(\s+)session\.query\((\w+)\)\.filter\((.*?)\)\.delete\(\)',
        r'\1await session.execute(\n\1    delete(\2).where(\3)\n\1)',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Add delete import if needed
    if 'delete(' in content and 'from sqlalchemy import' in content:
        content = re.sub(
            r'(from sqlalchemy import.*?)(\n)',
            r'\1, delete\2',
            content,
            count=1
        )
    
    # Write the fixed content back
    with open('/home/ubuntu/enterprise_system/backend/app/api/v1/endpoints/permissions.py', 'w') as f:
        f.write(content)
    
    print("Fixed AsyncSession issues in permissions endpoint")

if __name__ == "__main__":
    fix_permissions_async()

