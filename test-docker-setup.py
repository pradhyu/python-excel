#!/usr/bin/env python3
"""
Test script to validate Docker setup without requiring Docker daemon
"""

import os
import sys
from pathlib import Path
import subprocess
import json

def test_dockerfile_syntax():
    """Test Dockerfile syntax and structure"""
    print("🔍 Testing Dockerfile syntax...")
    
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        print("❌ Dockerfile not found")
        return False
    
    with open(dockerfile_path) as f:
        content = f.read()
    
    # Check for required instructions
    required_instructions = [
        "FROM python:",
        "WORKDIR /app",
        "COPY pyproject.toml",
        "RUN pip install",
        "USER exceluser",
        "CMD ["
    ]
    
    for instruction in required_instructions:
        if instruction not in content:
            print(f"❌ Missing required instruction: {instruction}")
            return False
    
    print("✅ Dockerfile syntax looks good")
    return True

def test_dockerignore():
    """Test .dockerignore file"""
    print("🔍 Testing .dockerignore...")
    
    dockerignore_path = Path(".dockerignore")
    if not dockerignore_path.exists():
        print("⚠️ .dockerignore not found (optional)")
        return True
    
    with open(dockerignore_path) as f:
        content = f.read()
    
    # Check for important exclusions
    important_exclusions = [
        ".git",
        "__pycache__",
        "*.pyc",
        ".venv",
        "*.log"
    ]
    
    for exclusion in important_exclusions:
        if exclusion not in content:
            print(f"⚠️ Consider adding to .dockerignore: {exclusion}")
    
    print("✅ .dockerignore looks good")
    return True

def test_docker_compose():
    """Test docker-compose.yml syntax"""
    print("🔍 Testing docker-compose.yml...")
    
    compose_path = Path("docker-compose.yml")
    if not compose_path.exists():
        print("⚠️ docker-compose.yml not found")
        return True
    
    try:
        import yaml
        with open(compose_path) as f:
            compose_data = yaml.safe_load(f)
        
        # Check structure
        if 'services' not in compose_data:
            print("❌ No 'services' section in docker-compose.yml")
            return False
        
        if 'excel-processor' not in compose_data['services']:
            print("❌ No 'excel-processor' service defined")
            return False
        
        print("✅ docker-compose.yml syntax is valid")
        return True
        
    except ImportError:
        print("⚠️ PyYAML not available, skipping YAML validation")
        return True
    except Exception as e:
        print(f"❌ docker-compose.yml syntax error: {e}")
        return False

def test_run_script():
    """Test docker-run.sh script"""
    print("🔍 Testing docker-run.sh script...")
    
    script_path = Path("docker-run.sh")
    if not script_path.exists():
        print("❌ docker-run.sh not found")
        return False
    
    # Check if executable
    if not os.access(script_path, os.X_OK):
        print("⚠️ docker-run.sh is not executable")
        print("   Run: chmod +x docker-run.sh")
    
    with open(script_path) as f:
        content = f.read()
    
    # Check for required functions
    required_functions = [
        "build_image()",
        "run_cli()",
        "run_notebook()",
        "show_help()"
    ]
    
    for func in required_functions:
        if func not in content:
            print(f"❌ Missing function: {func}")
            return False
    
    print("✅ docker-run.sh script looks good")
    return True

def test_sample_data():
    """Test sample data availability"""
    print("🔍 Testing sample data...")
    
    sample_dir = Path("sample_data")
    if not sample_dir.exists():
        print("⚠️ sample_data directory not found")
        return False
    
    # Check for Excel/CSV files
    excel_files = list(sample_dir.glob("*.xlsx")) + list(sample_dir.glob("*.xls"))
    csv_files = list(sample_dir.glob("*.csv"))
    
    if not excel_files and not csv_files:
        print("⚠️ No Excel or CSV files found in sample_data")
        return False
    
    print(f"✅ Found {len(excel_files)} Excel files and {len(csv_files)} CSV files")
    return True

def test_python_dependencies():
    """Test if Python dependencies are available"""
    print("🔍 Testing Python dependencies...")
    
    # Check pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("❌ pyproject.toml not found")
        return False
    
    # Try to import key modules
    try:
        import pandas
        print(f"✅ pandas {pandas.__version__} available")
    except ImportError:
        print("⚠️ pandas not available (required for Excel processing)")
    
    try:
        import openpyxl
        print(f"✅ openpyxl available")
    except ImportError:
        print("⚠️ openpyxl not available (required for .xlsx files)")
    
    return True

def simulate_docker_build():
    """Simulate Docker build process"""
    print("🔍 Simulating Docker build process...")
    
    # Check if all required files exist
    required_files = [
        "Dockerfile",
        "pyproject.toml",
        "excel_processor/__init__.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present for Docker build")
    return True

def test_notebook_integration():
    """Test notebook integration"""
    print("🔍 Testing notebook integration...")
    
    notebook_path = Path("Excel_DataFrame_Processor_Demo_Fixed.ipynb")
    if not notebook_path.exists():
        print("⚠️ Demo notebook not found")
        return False
    
    try:
        with open(notebook_path) as f:
            notebook_data = json.load(f)
        
        if 'cells' not in notebook_data:
            print("❌ Invalid notebook format")
            return False
        
        cell_count = len(notebook_data['cells'])
        print(f"✅ Demo notebook has {cell_count} cells")
        return True
        
    except Exception as e:
        print(f"❌ Notebook validation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🐳 Excel DataFrame Processor - Docker Setup Test")
    print("=" * 50)
    
    tests = [
        ("Dockerfile Syntax", test_dockerfile_syntax),
        ("Docker Ignore", test_dockerignore),
        ("Docker Compose", test_docker_compose),
        ("Run Script", test_run_script),
        ("Sample Data", test_sample_data),
        ("Python Dependencies", test_python_dependencies),
        ("Docker Build Simulation", simulate_docker_build),
        ("Notebook Integration", test_notebook_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Docker setup looks ready.")
        print("\n🚀 Next steps:")
        print("1. Start Docker daemon")
        print("2. Run: ./docker-run.sh build")
        print("3. Run: ./docker-run.sh run")
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)