"""Check university count"""
from config.settings import ALL_UNIVERSITIES

print(f"Total universities configured: {len(ALL_UNIVERSITIES)}")
print("\nUniversities:")
for i, name in enumerate(ALL_UNIVERSITIES.keys(), 1):
    print(f"{i}. {name}")
