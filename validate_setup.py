#!/usr/bin/env python3
"""
Validation script to check if the email outreach system is ready to use
"""
import sys
import os
from pathlib import Path

def check_imports():
    """Check if all required modules can be imported"""
    print("Checking imports...")
    try:
        from src import (
            SMTPAccount, SMTPManager,
            TemplateProcessor,
            ContactManager, Contact,
            EmailSender,
            FollowUpScheduler, FollowUpRule, FollowUpTrigger
        )
        from src.utils import load_smtp_accounts_from_env, setup_logging
        print("  ✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {str(e)}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")
    required_packages = {
        'dotenv': 'python-dotenv',
        'jinja2': 'jinja2',
        'email_validator': 'email-validator'
    }
    
    all_ok = True
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package} installed")
        except ImportError:
            print(f"  ✗ {package} not installed. Run: pip install {package}")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Check if .env file exists"""
    print("\nChecking configuration...")
    env_file = Path('.env')
    if env_file.exists():
        print("  ✓ .env file exists")
        # Check if it has content
        with open(env_file, 'r') as f:
            content = f.read().strip()
            if content and 'SMTP_HOST' in content:
                print("  ✓ .env file contains SMTP configuration")
                return True
            else:
                print("  ⚠ .env file exists but may be empty or incomplete")
                return False
    else:
        print("  ⚠ .env file not found (you can add it later)")
        print("     You can use --config-file with a JSON config instead")
        return False

def check_examples():
    """Check if example files exist"""
    print("\nChecking example files...")
    examples_dir = Path('examples')
    if not examples_dir.exists():
        print("  ✗ examples/ directory not found")
        return False
    
    required_files = [
        'contacts.csv',
        'subject_template.txt',
        'body_template.txt',
        'config.json',
        'followup_rules.json'
    ]
    
    all_exist = True
    for file in required_files:
        file_path = examples_dir / file
        if file_path.exists():
            print(f"  ✓ {file} exists")
        else:
            print(f"  ⚠ {file} not found (optional)")
            all_exist = False
    
    return True  # Examples are optional

def check_structure():
    """Check project structure"""
    print("\nChecking project structure...")
    required_dirs = [
        'src/smtp_manager',
        'src/template_engine',
        'src/contact_manager',
        'src/email_sender',
        'src/scheduler',
        'src/utils'
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✓ {dir_path}/ exists")
        else:
            print(f"  ✗ {dir_path}/ missing")
            all_ok = False
    
    return all_ok

def main():
    print("=" * 60)
    print("Email Outreach System - Setup Validation")
    print("=" * 60)
    
    checks = [
        ("Project Structure", check_structure),
        ("Dependencies", check_dependencies),
        ("Imports", check_imports),
        ("Configuration", check_env_file),
        ("Examples", check_examples),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Error during {name} check: {str(e)}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ System is ready to use!")
        print("\nNext steps:")
        print("  1. Add your SMTP credentials to .env file")
        print("  2. Prepare your contacts CSV file")
        print("  3. Create your email templates")
        print("  4. Run: python main.py send --help")
    else:
        print("⚠ Some checks failed. Please fix the issues above.")
        print("\nTo install dependencies:")
        print("  pip install -r requirements.txt")
    
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

