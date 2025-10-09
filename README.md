##   License
Academic research project - All rights reserved.

---

Automated research intelligence system for tracking emerging trends across Australasian universities using BERTopic and OpenAlex API.

##   Troubleshooting

##   Quarterly Updates

{{ ... }}
```
babcock-research-trends/
    config/
        themes.py              # Babcock's 9 strategic themes
        settings.py            # Configuration settings
    data/
        raw/                   # Raw collected papers
        processed/             # Preprocessed data
        exports/               # Generated reports
    tests/
        test_setup.py          # Environment validation script
        test_focused.py        # Targeted pipeline checks
    exploration/
        view_results.py        # Text summary explorer
    src/
        openalex_collector.py # OpenAlex data collection
        preprocessor.py        # Data preprocessing
        topic_analyzer.py      # BERTopic topic modeling
        theme_mapper.py        # Map topics to Babcock themes

    .env                       # Your configuration (create this)
    .env.example               # Configuration template
    requirements.txt           # Python dependencies
    README.md                  # This file