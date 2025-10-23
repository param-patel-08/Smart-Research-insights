"""
Test script to verify Babcock Research Trends system setup
Run this to check if everything is configured correctly
"""

import os
import sys


# Ensure project root is importable when running from tests/
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def test_imports():
    """Test if all required packages are installed"""
    print("\n" + "=" * 80)
    print("TESTING PACKAGE IMPORTS")
    print("=" * 80)

    packages = {
        "pandas": "pandas",
        "numpy": "numpy",
        "requests": "requests",
        "bertopic": "BERTopic",
        "sentence_transformers": "sentence-transformers",
        "umap": "umap-learn",
        "hdbscan": "hdbscan",
        "streamlit": "streamlit",
        "plotly": "plotly",
        "sklearn": "scikit-learn",
        "tqdm": "tqdm",
        "dotenv": "python-dotenv",
    }

    failed = []

    for module, package in packages.items():
        try:
            __import__(module)
            print(f"  {package}")
        except ImportError:
            print(f"  {package} - NOT INSTALLED")
            failed.append(package)

    if failed:
        print(f"\n  Missing packages: {', '.join(failed)}")
        print(f"Install with: pip install {' '.join(failed)}")
        return False

    print("\n  All packages installed successfully!")
    return True


def test_config():
    """Test configuration files"""
    print("\n" + "=" * 80)
    print("TESTING CONFIGURATION")
    print("=" * 80)

    try:
        from config.themes import BABCOCK_THEMES
        from config.settings import (
            ANALYSIS_END_DATE,
            ANALYSIS_START_DATE,
            ALL_UNIVERSITIES,
            OPENALEX_EMAIL,
        )

        print(f"  Themes loaded: {len(BABCOCK_THEMES)} themes")
        print(f"  Universities configured: {len(ALL_UNIVERSITIES)}")
        print(f"  Date range: {ANALYSIS_START_DATE.date()} to {ANALYSIS_END_DATE.date()}")
        print(f"  OpenAlex email: {OPENALEX_EMAIL}")

        if OPENALEX_EMAIL == "your.email@example.com":
            print("\n    WARNING: Please update OPENALEX_EMAIL in .env file!")
            print("   Create .env file with: OPENALEX_EMAIL=your.email@university.edu")
            return False

        return True

    except Exception as exc:  # pragma: no cover - diagnostic output
        print(f"  Configuration error: {exc}")
        return False


def test_directories():
    """Test if required directories exist"""
    print("\n" + "=" * 80)
    print("TESTING DIRECTORY STRUCTURE")
    print("=" * 80)

    required_dirs = [
        "config",
        "src",
        "data",
        "data/raw",
        "data/processed",
        "data/exports",
        "models",
        "logs",
        "tests",
        "exploration",
    ]

    all_exist = True
    for directory in required_dirs:
        if os.path.exists(os.path.join(ROOT_DIR, directory)):
            print(f"  {directory}/")
        else:
            print(f"  {directory}/ - MISSING")
            all_exist = False

    if not all_exist:
        print("\n    Some directories are missing. They will be created automatically when you run the scripts.")

    return True


def test_modules():
    """Test if custom modules can be imported"""
    print("\n" + "=" * 80)
    print("TESTING CUSTOM MODULES")
    print("=" * 80)

    try:
        from src.paper_collector import PaperCollector  # noqa: F401
        print("✓ paper_collector.py")

        from src.paper_preprocessor import PaperPreprocessor  # noqa: F401
        print("✓ paper_preprocessor.py")

        from config.themes import BABCOCK_THEMES  # noqa: F401
        print("✓ themes.py")

        from config.settings import ALL_UNIVERSITIES  # noqa: F401
        print("✓ settings.py")

        return True

    except Exception as exc:  # pragma: no cover - diagnostic output
        print(f"  Module import failed: {exc}")
        return False


def test_openalex_connection():
    """Test connection to OpenAlex API"""
    print("\n" + "=" * 80)
    print("TESTING OPENALEX API CONNECTION")
    print("=" * 80)

    try:
        import requests
        from config.settings import OPENALEX_EMAIL

        url = "https://api.openalex.org/works"
        params = {
            "filter": "institutions.id:I145311948",  # University of Melbourne
            "per-page": 1,
            "mailto": OPENALEX_EMAIL,
        }

        print("Testing API connection...")
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            count = data.get("meta", {}).get("count", 0)
            print("  OpenAlex API connection successful!")
            print(f"  Test query returned {count:,} total papers")
            return True

        print(f"  API returned status code: {response.status_code}")
        return False

    except Exception as exc:  # pragma: no cover - diagnostic output
        print(f"  API connection failed: {exc}")
        return False


def main():
    """Run all setup tests"""
    print("\n" + "=" * 80)
    print("BABCOCK RESEARCH TRENDS - SYSTEM TEST")
    print("=" * 80)

    results = []
    results.append(("Package Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Directories", test_directories()))
    results.append(("Custom Modules", test_modules()))
    results.append(("OpenAlex API", test_openalex_connection()))

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        status = "  PASS" if passed else "  FAIL"
        print(f"{status} - {test_name}")

    if all(result[1] for result in results):
        print("\n" + "=" * 80)
        print("  ALL TESTS PASSED! System is ready to use.")
        print("=" * 80)
        print("\nNext steps:")
        print("1. python run_full_analysis.py           # Execute full pipeline")
        print("2. streamlit run dashboard/app.py        # Launch interactive dashboard")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("  SOME TESTS FAILED. Please fix the issues above.")
        print("=" * 80)


if __name__ == "__main__":
    main()