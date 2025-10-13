# Conference Papers & Data Quality Fixes

**Date:** October 13, 2025  
**Status:** ✅ Applied

---

## 🎯 Issues Fixed

### 1. **Conference Papers Not Identified** ✅
**Problem:** OpenAlex classifies both journal and conference papers as `type: article`, making them indistinguishable.

**Solution:** Extract `primary_location.source.type` field which contains:
- `journal` = Journal article
- `conference` = Conference paper
- Other values for books, reports, etc.

**Changes:**
- Added `source_type` column to collected data
- Updated `_parse_work()` to extract `source.type` from `primary_location`
- Updated `_calculate_confidence()` to use `source_type` for accurate scoring

---

### 2. **Misclassified Papers (Relevance = 0.0)** ✅
**Problem:** Papers like "AI for next generation computing" were assigned to Cybersecurity theme with 0.0 relevance score.

**Root Cause:** 
- Papers fetched during theme collection get tagged with that theme
- Generic keywords (e.g., "computing", "cloud") match multiple themes
- Relevance scorer correctly identifies mismatch but papers still included

**Solution:** Filter out papers with relevance < 0.1 (10%)

**Changes:**
- Changed `min_relevance` from 0.0 to 0.1 in collection
- Added post-collection filter to remove papers with relevance < 0.1
- Log how many papers were filtered out

---

### 3. **Improved Confidence Scoring for Conferences** ✅
**Problem:** Confidence scoring didn't properly distinguish between journals and conferences.

**Solution:** Updated `_calculate_confidence()` to:
1. **Prioritize `source_type`** over `pub_type` (more reliable)
2. **Proper conference scoring:**
   - Conference with 3+ citations = 0.8 (medium-high)
   - Conference with 1-2 citations = 0.6 (medium)
   - Conference with 0 citations = 0.4 (medium-low)
3. **Added review article handling** (treat like journals)

---

## 📊 Expected Results After Fixes

### Conference Paper Identification:
**Before:**
```csv
type,source_type,confidence_score
article,,0.8
article,,1.0
```

**After:**
```csv
type,source_type,confidence_score
article,journal,1.0
article,conference,0.6
article,journal,0.8
```

### Data Quality:
**Before:**
- Papers with 0.0 relevance included
- "AI paper" in Cybersecurity theme ❌

**After:**
- Papers with <0.1 relevance filtered out
- Only relevant papers per theme ✅

### Confidence Distribution:
**Expected with conferences:**
- 🟢 1.0 (High): 15-20% (well-cited journals)
- 🟡 0.8 (Med-High): 25-30% (recent journals + cited conferences)
- 🟡 0.6 (Medium): 25-30% (recent conferences + new journals)
- 🟠 0.4 (Med-Low): 10-15% (new conferences + working papers)
- 🔴 0.2 (Low): 5-10% (preprints)

---

## 🔧 Technical Details

### New Column: `source_type`
**Values:**
- `journal` - Published in academic journal
- `conference` - Published in conference proceedings
- `repository` - Preprint repository
- Empty string - Unknown/other

### Relevance Filtering
**Threshold:** 0.1 (10% relevance minimum)

**Why 0.1?**
- Papers with 0.0-0.09 relevance are likely misclassified
- Papers with 0.1+ have at least some thematic connection
- Balances precision (accuracy) with recall (coverage)

### Confidence Calculation Logic
```python
def _calculate_confidence(pub_type, citations, source_type):
    if source_type == 'journal':
        if citations >= 5: return 1.0
        elif citations >= 1: return 0.8
        else: return 0.6
    
    elif source_type == 'conference':
        if citations >= 3: return 0.8
        elif citations >= 1: return 0.6
        else: return 0.4
    
    elif 'preprint' in pub_type:
        return 0.2
    
    # ... other cases
```

---

## 📈 Impact on Collection

### Papers Collected:
**Before fixes:**
- ~200-250 papers
- Mix of journals, reviews, preprints
- No conference identification
- Some misclassified papers

**After fixes:**
- ~180-230 papers (slightly fewer due to relevance filter)
- Proper journal/conference distinction
- Higher quality dataset
- Accurate confidence scores

### Conference Papers:
**Expected percentage:** 20-35% of total papers
- CS/AI/Cybersecurity: 40-50% conferences
- Engineering/Energy: 20-30% conferences
- Other themes: 10-20% conferences

---

## ✅ Verification Checklist

After next collection run, verify:
- [ ] `source_type` column exists in `papers_raw.csv`
- [ ] `source_type` contains values: `journal`, `conference`, etc.
- [ ] No papers with `relevance_score < 0.1`
- [ ] Conference papers have appropriate confidence scores (0.4-0.8)
- [ ] Journal papers have appropriate confidence scores (0.6-1.0)
- [ ] Distribution matches expected percentages

---

## 🚀 Ready to Run

All fixes applied! Next collection will:
1. ✅ Properly identify conference papers
2. ✅ Filter out misclassified papers
3. ✅ Assign accurate confidence scores
4. ✅ Provide clean, high-quality dataset

Run the collection:
```powershell
.venv\Scripts\python run_full_analysis.py
# Choose option 3 (full collection)
```
