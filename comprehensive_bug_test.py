#!/usr/bin/env python3
"""
Comprehensive Bug Detection and Testing Script
Tests all microservices for import issues, missing dependencies, and logic errors
"""

import os
import sys
import importlib.util
import traceback
from pathlib import Path

def test_service_imports(service_path, service_name):
    """Test if a service can be imported without errors"""
    print(f"\n🔍 Testing {service_name}...")
    
    try:
        # Add service path to Python path
        sys.path.insert(0, str(service_path))
        
        # Try to import the main module
        main_file = service_path / "src" / "main.py"
        if main_file.exists():
            spec = importlib.util.spec_from_file_location("main", main_file)
            if spec and spec.loader:
                # Set minimal environment variables to avoid security errors
                os.environ.setdefault(f"{service_name.upper()}_SECRET", "test-secret-key")
                os.environ.setdefault("OPENAI_API_KEY", "test-key")
                os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(f"✅ {service_name}: Import successful")
                return True
        else:
            print(f"❌ {service_name}: main.py not found")
            return False
            
    except ImportError as e:
        print(f"❌ {service_name}: Import error - {e}")
        return False
    except Exception as e:
        print(f"⚠️ {service_name}: Other error - {e}")
        return False
    finally:
        # Clean up path
        if str(service_path) in sys.path:
            sys.path.remove(str(service_path))

def find_missing_dependencies():
    """Find missing Python dependencies across all services"""
    print("\n🔍 Checking for missing dependencies...")
    
    services_dir = Path("enterprise_system/microservices")
    missing_deps = set()
    
    for service_dir in services_dir.iterdir():
        if service_dir.is_dir() and not service_dir.name.startswith('.'):
            # Look for Python files
            for py_file in service_dir.rglob("*.py"):
                if "venv" in str(py_file):
                    continue
                    
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        
                    # Extract import statements
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('import ') or line.startswith('from '):
                            # Extract module name
                            if line.startswith('import '):
                                module = line.split()[1].split('.')[0]
                            elif line.startswith('from '):
                                module = line.split()[1].split('.')[0]
                            
                            # Check if it's a third-party module
                            if module not in ['os', 'sys', 'json', 'datetime', 'typing', 'pathlib', 'uuid', 'io']:
                                try:
                                    __import__(module)
                                except ImportError:
                                    missing_deps.add(module)
                                    
                except Exception as e:
                    print(f"⚠️ Error reading {py_file}: {e}")
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
    else:
        print("✅ All dependencies available")
    
    return missing_deps

def test_database_operations():
    """Test database operations for proper error handling"""
    print("\n🔍 Testing database operations...")
    
    backend_dir = Path("enterprise_system/backend")
    issues = []
    
    for py_file in backend_dir.rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Check for database commits without proper error handling
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'db.session.commit()' in line or 'db.commit()' in line:
                    # Check if there's a try-except block around it
                    context = '\n'.join(lines[max(0, i-5):i+5])
                    if 'try:' not in context or 'except' not in context:
                        issues.append(f"{py_file}:{i+1} - Unprotected database commit")
                    elif 'rollback' not in context:
                        issues.append(f"{py_file}:{i+1} - Missing rollback in error handling")
                        
        except Exception as e:
            print(f"⚠️ Error analyzing {py_file}: {e}")
    
    if issues:
        print("❌ Database operation issues found:")
        for issue in issues[:5]:  # Show first 5 issues
            print(f"  - {issue}")
    else:
        print("✅ Database operations properly handled")
    
    return issues

def main():
    """Main testing function"""
    print("🚀 COMPREHENSIVE BUG DETECTION STARTED")
    print("=" * 50)
    
    # Test microservices
    services_dir = Path("enterprise_system/microservices")
    service_results = {}
    
    if services_dir.exists():
        for service_dir in services_dir.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith('.'):
                # Find the actual service directory (some have nested structure)
                main_file = None
                for subdir in [service_dir, service_dir / f"{service_dir.name}_ai_service"]:
                    if (subdir / "src" / "main.py").exists():
                        main_file = subdir
                        break
                
                if main_file:
                    service_results[service_dir.name] = test_service_imports(main_file, service_dir.name)
                else:
                    print(f"❌ {service_dir.name}: No main.py found")
                    service_results[service_dir.name] = False
    
    # Test for missing dependencies
    missing_deps = find_missing_dependencies()
    
    # Test database operations
    db_issues = test_database_operations()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    successful_services = sum(1 for result in service_results.values() if result)
    total_services = len(service_results)
    
    print(f"✅ Services working: {successful_services}/{total_services}")
    print(f"❌ Missing dependencies: {len(missing_deps)}")
    print(f"⚠️ Database issues: {len(db_issues)}")
    
    if successful_services == total_services and not missing_deps and not db_issues:
        print("\n🎉 ALL TESTS PASSED - NO CRITICAL BUGS FOUND!")
        return True
    else:
        print("\n🔧 ISSUES FOUND - NEED FIXES")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

