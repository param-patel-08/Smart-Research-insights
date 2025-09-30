"""
Quick launcher for Streamlit dashboard
"""

import os
import sys
import subprocess

def check_data_exists():
    """Check if analysis data exists"""
    required_files = [
        'data/processed/papers_with_topics.csv',
        'data/processed/trend_analysis.json',
        'models/topic_theme_mapping.json'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    return missing

def main():
    print("="*80)
    print("  BABCOCK RESEARCH TRENDS - DASHBOARD LAUNCHER")
    print("="*80)
    print()
    
    # Check if data exists
    missing = check_data_exists()
    
    if missing:
        print("❌ Analysis data not found!")
        print()
        print("Missing files:")
        for file in missing:
            print(f"  - {file}")
        print()
        print("Please run the analysis first:")
        print("  python run_full_analysis.py")
        print()
        sys.exit(1)
    
    print("✓ Data files found")
    print()
    print("🚀 Launching Streamlit dashboard...")
    print()
    print("The dashboard will open in your browser automatically.")
    print("If not, go to: http://localhost:8501")
    print()
    print("Press Ctrl+C to stop the dashboard")
    print("="*80)
    print()
    
    # Launch streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "dashboard/app.py",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")
    except Exception as e:
        print(f"\n❌ Error launching dashboard: {e}")
        print("\nTry running manually:")
        print("  streamlit run dashboard/app.py")

if __name__ == "__main__":
    main()