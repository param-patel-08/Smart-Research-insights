## 📄 License
Academic research project - All rights reserved.

---

Note: `view_results_fixed.py` is a duplicate of `view_results.py` and will be removed in a future cleanup. Please use `view_results.py`.

Automated research intelligence system for tracking emerging trends across Australasian universities using BERTopic and OpenAlex API.

## 🐛 Troubleshooting

## 🔄 Quarterly Updates

- Python 3.9 or higher
- pip package manager
- Your email address (for OpenAlex API polite pool)

## 📋 Prerequisites

- Python 3.9 or higher
- pip package manager
- Your email address (for OpenAlex API polite pool)

## 🚀 Quick Start

### 1. Installation

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root with your OpenAlex polite pool email:

```
OPENALEX_EMAIL=your.email@university.edu
```

### 3. Run the Pipeline

Start the end-to-end pipeline and generate all outputs:

```bash
python run_full_analysis.py
```

You'll be prompted to choose scope (quick/medium/full). You can also pass 1/2/3 as an argument.

When finished, view a text summary:

```bash
python view_results.py
```

Launch the interactive dashboard:

```bash
python launch_dashboard.py
```

## 📁 Project Structure

```
babcock-research-trends/
├── config/
│   ├── themes.py              # Babcock's 9 strategic themes
│   └── settings.py            # Configuration settings
├── data/
│   ├── raw/                   # Raw collected papers
│   ├── processed/             # Preprocessed data
│   └── exports/               # Generated reports
├── src/
│   ├── openalex_collector.py # OpenAlex data collection
│   ├── preprocessor.py        # Data preprocessing
│   ├── topic_analyzer.py      # BERTopic topic modeling
│   ├── theme_mapper.py        # Map topics to Babcock themes
│   └── trend_analyzer.py      # Theme and topic trends

├── .env                       # Your configuration (create this)
├── .env.example               # Configuration template
├── requirements.txt           # Python dependencies
└── README.md                  # This file