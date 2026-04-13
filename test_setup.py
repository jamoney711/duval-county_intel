#!/usr/bin/env python3
"""
Test and validation script for Duval County scraper
Run this to verify setup and test individual components
"""

import sys
import json
from pathlib import Path

def test_file_structure():
    """Verify all required files exist"""
    print("Testing file structure...")
    
    required_files = [
        'scraper/fetch.py',
        'scraper/requirements.txt',
        'dashboard/index.html',
        'dashboard/records.json',
        '.github/workflows/scrape.yml',
        'README.md'
    ]
    
    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
            print(f"  ❌ Missing: {file_path}")
        else:
            print(f"  ✓ Found: {file_path}")
    
    if missing:
        print(f"\n❌ FAIL: {len(missing)} files missing")
        return False
    else:
        print("\n✓ PASS: All required files present")
        return True

def test_json_structure():
    """Verify JSON files have correct structure"""
    print("\nTesting JSON structure...")
    
    try:
        with open('dashboard/records.json', 'r') as f:
            data = json.load(f)
        
        required_keys = ['fetched_at', 'source', 'date_range', 'total', 'with_address', 'records']
        missing_keys = [k for k in required_keys if k not in data]
        
        if missing_keys:
            print(f"  ❌ Missing keys in records.json: {missing_keys}")
            return False
        
        print("  ✓ records.json structure valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON in records.json: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error reading records.json: {e}")
        return False

def test_imports():
    """Test if required Python packages can be imported"""
    print("\nTesting Python imports...")
    
    packages = [
        ('requests', 'requests'),
        ('beautifulsoup4', 'bs4'),
        ('lxml', 'lxml'),
        ('dbfread', 'dbfread'),
        ('playwright', 'playwright')
    ]
    
    all_ok = True
    for pkg_name, import_name in packages:
        try:
            __import__(import_name)
            print(f"  ✓ {pkg_name}")
        except ImportError:
            print(f"  ❌ {pkg_name} not installed")
            all_ok = False
    
    if all_ok:
        print("\n✓ PASS: All packages available")
    else:
        print("\n❌ FAIL: Some packages missing")
        print("Run: pip install -r scraper/requirements.txt")
    
    return all_ok

def test_workflow_yaml():
    """Verify GitHub Actions workflow syntax"""
    print("\nTesting workflow YAML...")
    
    try:
        import yaml
        with open('.github/workflows/scrape.yml', 'r') as f:
            workflow = yaml.safe_load(f)
        
        if 'on' not in workflow:
            print("  ❌ Missing 'on' trigger in workflow")
            return False
        
        if 'jobs' not in workflow:
            print("  ❌ Missing 'jobs' in workflow")
            return False
        
        print("  ✓ Workflow YAML valid")
        return True
        
    except ImportError:
        print("  ⚠ PyYAML not installed, skipping YAML validation")
        return True
    except Exception as e:
        print(f"  ❌ Workflow YAML error: {e}")
        return False

def show_summary():
    """Display helpful summary and next steps"""
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60)
    print("""
📁 Files Created:
   ✓ scraper/fetch.py          - Main scraper logic
   ✓ scraper/requirements.txt  - Python dependencies  
   ✓ dashboard/index.html      - Dashboard UI
   ✓ dashboard/records.json    - Initial data file
   ✓ .github/workflows/scrape.yml - GitHub Actions automation

🚀 Next Steps:
   1. Push these files to GitHub
   2. Enable GitHub Actions in repository settings
   3. Enable GitHub Pages (Settings → Pages → Source: GitHub Actions)
   4. Run workflow manually (Actions → Run workflow)
   5. Wait 5-10 minutes
   6. Access dashboard at: https://[username].github.io/[repo]/

💡 Local Testing:
   pip install -r scraper/requirements.txt
   python -m playwright install chromium
   python scraper/fetch.py

📖 Full documentation in README.md
""")

def main():
    """Run all tests"""
    print("Duval County Scraper Validation\n")
    
    results = []
    results.append(test_file_structure())
    results.append(test_json_structure())
    results.append(test_imports())
    results.append(test_workflow_yaml())
    
    print("\n" + "="*60)
    
    if all(results):
        print("✅ ALL TESTS PASSED!")
        show_summary()
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"❌ {failed} TEST(S) FAILED")
        print("\nPlease fix the issues above before proceeding.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
