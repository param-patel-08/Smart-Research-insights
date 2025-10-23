"""
Quick fix for import errors
Creates __init__.py files and tests imports
"""

import os
import sys

print("="*80)
print("FIXING IMPORT ISSUES")
print("="*80)

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Create __init__.py files
print("\n1. Creating __init__.py files...")

init_files = [
    'config/__init__.py',
    'src/__init__.py',
    'dashboard/__init__.py'
]

for file in init_files:
    os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, 'w') as f:
        f.write('# Auto-generated\n')
    print(f"     Created {file}")

print("\n2. Testing imports...")

# Test config imports
try:
    from config import settings
    print("     config.settings imported")
except Exception as e:
    print(f"     config.settings failed: {e}")

try:
    from config import themes
    print("     config.themes imported")
except Exception as e:
    print(f"     config.themes failed: {e}")

# Test src imports
try:
    from src import theme_based_collector
    print("✓    src.theme_based_collector imported")
except Exception as e:
    print(f"✗    src.theme_based_collector failed: {e}")

try:
    from src import paper_preprocessor
    print("✓    src.paper_preprocessor imported")
except Exception as e:
    print(f"✗    src.paper_preprocessor failed: {e}")

print("\n3. Checking file existence...")

required_files = [
    'config/settings.py',
    'config/themes.py',
    'src/theme_based_collector.py',
    'src/paper_preprocessor.py',
    'src/topic_analyzer.py',
    'src/theme_mapper.py',
    'src/trend_analyzer.py',
    '.env'
]

all_exist = True
for file in required_files:
    exists = os.path.exists(file)
    status = " " if exists else " "
    print(f"   {status} {file}")
    if not exists:
        all_exist = False

print("\n" + "="*80)

if all_exist:
    print("  ALL FILES EXIST")
    print("\nYou can now run:")
    print("  python run_full_analysis.py")
else:
    print("  SOME FILES ARE MISSING")
    print("\nPlease ensure all files are in place.")

print("="*80)