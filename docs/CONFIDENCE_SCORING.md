# Confidence Scoring System

## Overview

The Research Trend Analyzer assigns a **confidence score** (0.2 to 1.0) to each collected paper based on:
1. **Publication type** (journal, conference, preprint, etc.)
2. **Citation count** (validation by research community)

This allows us to collect ALL relevant research while providing transparency about data quality and reliability.

---

## Confidence Levels

### 🟢 **High Confidence (1.0)**
**Criteria:** Journal articles with 5+ citations

**What this means:**
- Peer-reviewed by experts
- Published in academic journal
- Validated by research community (5+ citations)
- Established, reliable findings

**Use cases:**
- High-stakes decision making
- Policy recommendations
- Funding allocation
- Strategic planning

**Example:** A 2021 IEEE Transactions paper on cybersecurity with 12 citations

---

### 🟡 **Medium-High Confidence (0.8)**
**Criteria:** 
- Journal articles with 1-4 citations, OR
- Conference papers with 3+ citations

**What this means:**
- Peer-reviewed
- Some community validation
- Reliable but less established

**Use cases:**
- Trend identification
- Research direction planning
- Emerging topic detection

**Example:** A 2023 Nature Energy paper with 2 citations, or a NeurIPS 2022 paper with 5 citations

---

### 🟡 **Medium Confidence (0.6)**
**Criteria:**
- Conference papers with 1-2 citations, OR
- Recent journal articles with 0 citations

**What this means:**
- Peer-reviewed
- Very recent (may not have time to accumulate citations)
- Minimal community validation yet

**Use cases:**
- Cutting-edge research tracking
- Early trend signals
- Emerging technology monitoring

**Example:** A 2024 CVPR paper with 1 citation, or a 2024 Science Robotics paper just published

---

### 🟠 **Medium-Low Confidence (0.4)**
**Criteria:**
- Conference papers with 0 citations, OR
- Working papers

**What this means:**
- Peer-reviewed (for conferences)
- Very recent or preliminary
- No community validation yet

**Use cases:**
- Horizon scanning
- Early warning signals
- Exploratory research

**Example:** A 2024 ICML paper just published, or a working paper from a research lab

---

### 🔴 **Low Confidence (0.2)**
**Criteria:** Preprints (arXiv, bioRxiv, etc.)

**What this means:**
- **NOT peer-reviewed**
- May contain errors or incomplete analysis
- Represents current thinking but unvalidated

**Use cases:**
- Very early trend detection
- Monitoring cutting-edge developments
- Identifying emerging researchers/topics

**Example:** An arXiv preprint uploaded last month

---

## How Confidence Scores Are Used

### 1. **Data Quality Dashboard**
- Filter papers by minimum confidence level
- View distribution of confidence scores
- Identify high-quality vs. exploratory research

### 2. **Trend Analysis**
- Weight trends by confidence (high-confidence papers = stronger signal)
- Separate "established trends" from "emerging signals"
- Risk-adjusted trend forecasting

### 3. **Topic Modeling**
- All papers contribute to topic discovery
- High-confidence papers anchor topics
- Low-confidence papers show emerging directions

### 4. **Reporting**
- Clearly label findings with confidence levels
- Provide separate insights for different confidence tiers
- Transparent about data quality

---

## Publication Type Breakdown

### Journal Articles
**Characteristics:**
- Peer-reviewed (2-3 expert reviewers)
- 6-18 month publication timeline
- Rigorous quality control
- Considered "gold standard"

**Confidence:** 0.6 to 1.0 (based on citations)

**Examples:** Nature, Science, IEEE Transactions, PLOS ONE

---

### Conference Papers
**Characteristics:**
- Peer-reviewed (2-3 reviewers)
- 3-6 month publication timeline
- Faster than journals
- **Dominant in CS/Engineering** (often more prestigious than journals!)

**Confidence:** 0.4 to 0.8 (based on citations)

**Examples:** NeurIPS, CVPR, ICML, ACM CHI, IEEE INFOCOM

---

### Preprints
**Characteristics:**
- **NOT peer-reviewed**
- Immediate publication (days)
- May later become journal/conference papers
- Growing rapidly in all fields

**Confidence:** 0.2 (fixed)

**Examples:** arXiv, bioRxiv, SSRN

---

### Working Papers
**Characteristics:**
- Preliminary research
- Shared for feedback
- May change significantly
- Common in economics/social sciences

**Confidence:** 0.4 (fixed)

---

## Expected Distribution

Based on typical AU/NZ research output in technical fields:

| Confidence | Expected % | Publication Types |
|------------|-----------|-------------------|
| 1.0 (High) | 15-25% | Well-cited journals |
| 0.8 (Med-High) | 25-35% | Recent journals, top conferences |
| 0.6 (Medium) | 20-30% | Recent conferences, very new journals |
| 0.4 (Med-Low) | 15-25% | Brand new conferences, working papers |
| 0.2 (Low) | 5-10% | Preprints |

**Mean confidence: ~0.65-0.75**

---

## Filtering Recommendations

### For Strategic Decisions (High Stakes)
**Minimum confidence: 0.8**
- Only well-validated research
- ~40-60% of papers
- Conservative, reliable insights

### For Trend Analysis (Balanced)
**Minimum confidence: 0.6**
- Peer-reviewed research
- ~70-85% of papers
- Good balance of quality and coverage

### For Horizon Scanning (Exploratory)
**Minimum confidence: 0.4**
- All peer-reviewed + working papers
- ~90-95% of papers
- Early signals, emerging topics

### For Cutting-Edge Monitoring (Comprehensive)
**Minimum confidence: 0.2**
- Everything including preprints
- 100% of papers
- Maximum coverage, accept some noise

---

## Implementation Details

### Calculation Logic
```python
def _calculate_confidence(pub_type, citations):
    if 'journal' in pub_type:
        if citations >= 5: return 1.0
        elif citations >= 1: return 0.8
        else: return 0.6
    
    elif 'proceedings' in pub_type or 'conference' in pub_type:
        if citations >= 3: return 0.8
        elif citations >= 1: return 0.6
        else: return 0.4
    
    elif 'preprint' in pub_type:
        return 0.2
    
    elif 'working' in pub_type:
        return 0.4
    
    else:  # Unknown types
        if citations >= 5: return 0.8
        elif citations >= 1: return 0.6
        else: return 0.4
```

### Storage
- Confidence score stored in `confidence_score` column
- Range: 0.2 to 1.0
- Type: float

### Dashboard Integration
- Filter slider: "Minimum Confidence Level"
- Color coding: Green (≥0.8), Yellow (0.6-0.8), Orange (0.4-0.6), Red (<0.4)
- Separate tabs for different confidence tiers
- Weighted metrics (e.g., "confidence-weighted citation impact")

---

## Benefits of This Approach

✅ **Maximum Coverage** - Collect all relevant research, not just journals
✅ **Transparency** - Clear quality indicators for each paper
✅ **Flexibility** - Users can adjust confidence thresholds based on needs
✅ **Early Signals** - Catch emerging trends from conferences and preprints
✅ **Risk Management** - Know which findings are well-validated vs. exploratory
✅ **Better for CS/Engineering** - Properly weights conference papers
✅ **Trend Detection** - Separate established trends from emerging signals

---

## Future Enhancements

1. **Venue prestige** - Weight by journal/conference ranking (e.g., A*, Q1)
2. **Author reputation** - Consider h-index of authors
3. **Institutional prestige** - Weight by university ranking
4. **Recency decay** - Adjust confidence for very old papers
5. **Field-specific** - Different thresholds for different disciplines
6. **Machine learning** - Train model to predict paper quality

---

## References

- OpenAlex documentation on publication types
- Citation analysis best practices
- Peer review standards in CS/Engineering
- Preprint usage guidelines
