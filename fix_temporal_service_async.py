#!/usr/bin/env python3
"""
Script to fix all AsyncSession compatibility issues in temporal permissions service.
"""

import re

def fix_temporal_service_async():
    """Fix all AsyncSession issues in temporal permissions service."""
    
    # Read the file
    with open('/home/ubuntu/enterprise_system/backend/app/services/temporal_permissions.py', 'r') as f:
        content = f.read()
    
    # Add select import if not present
    if 'from sqlalchemy import select' not in content:
        content = re.sub(
            r'(from sqlalchemy\.orm import.*?\n)',
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
    
    # Replace session.query(Model).options(...).filter(...).all() patterns
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*session\.query\((\w+)\)\.options\((.*?)\)\.filter\((.*?)\)\.all\(\)',
        r'\1\2_result = await session.execute(\n\1    select(\3).options(\4).where(\5)\n\1)\n\1\2 = \2_result.scalars().all()',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Replace query = session.query(...).filter(...) patterns
    content = re.sub(
        r'(\s+)query\s*=\s*session\.query\((\w+)\)\.filter\((.*?)\)',
        r'\1query = select(\2).where(\3)',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Replace query.all() with session.execute(query).scalars().all()
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*query\.all\(\)',
        r'\1\2_result = await session.execute(query)\n\1\2 = \2_result.scalars().all()',
        content,
        flags=re.MULTILINE
    )
    
    # Write the fixed content back
    with open('/home/ubuntu/enterprise_system/backend/app/services/temporal_permissions.py', 'w') as f:
        f.write(content)
    
    print("Fixed AsyncSession issues in temporal permissions service")

if __name__ == "__main__":
    fix_temporal_service_async()

