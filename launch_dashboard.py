"""
Quick launcher for Streamlit dashboard
"""

import os
import sys
import subprocess

# Use configured paths with safe fallbacks
try:
    from config.settings import (
        PROCESSED_PAPERS_CSV,
        TREND_ANALYSIS_PATH,
        TOPIC_MAPPING_PATH,
    )
except Exception:
    PROCESSED_PAPERS_CSV = 'data/processed/papers_processed.csv'
    TREND_ANALYSIS_PATH = 'data/processed/trend_analysis.csv'
    TOPIC_MAPPING_PATH = 'data/processed/topic_mapping.csv'


def check_data_exists():
    """Check if analysis data exists using configured paths"""
    required_files = [
        PROCESSED_PAPERS_CSV,
        TREND_ANALYSIS_PATH,
        TOPIC_MAPPING_PATH,
    ]
    missing = [f for f in required_files if not os.path.exists(f)]
    return missing


def main():
    print("=" * 80)
    print("  BABCOCK RESEARCH TRENDS - DASHBOARD LAUNCHER")
    print("=" * 80)
    print()

    missing = check_data_exists()
    if missing:
        print("❌ Analysis data not found!\n")
        print("Missing files:")
        for f in missing:
            print(f"  - {f}")
        print()
        print("Please run the analysis first:")
        print("  python run_full_analysis.py 1   # quick test")
        print("  python run_full_analysis.py 3   # full run")
        print()
        sys.exit(1)

    print("Data files found\n")
    print("Launching Streamlit dashboard...\n")
    print("The dashboard will open in your browser automatically.")
    print("If not, go to: http://localhost:8501\n")
    print("Press Ctrl+C to stop the dashboard")
    print("=" * 80)
    print()

    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "dashboard/app.py",
            "--server.headless", "false",
        ])
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")
    except Exception as e:
        print(f"\n❌ Error launching dashboard: {e}")
        print("\nTry running manually:")
        print("  streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()