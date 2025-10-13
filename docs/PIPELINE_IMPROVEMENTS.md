# Pipeline Improvements & Optimization Plan

**Date:** October 13, 2025  
**Status:** 🔴 CRITICAL - Needs Implementation

---

## 🚨 **CRITICAL ISSUES IDENTIFIED**

### Issue 1: Too Few Papers Collected (140 → 133 final)
**Root Causes:**
1. **Overly Aggressive Deduplication** - Removed 58 papers (29.3%)
2. **Relevance Filtering Too Strict** - Removed 18 papers with <10% relevance
3. **No Papers for 7 Themes** - BERTopic assigned all papers to only 2 themes
4. **Sparse Themes** - Autonomous_Systems (0), Marine_Naval (0) had 0 papers collected

### Issue 2: Inefficient Collection Process
**Problems:**
1. **No Checkpointing** - 3+ hour collection lost if interrupted
2. **Repeated Institution Resolution** - 44 universities × 9 themes = 396 API calls (wasteful!)
3. **Sequential Theme Processing** - Could be parallelized
4. **No Progress Persistence** - Can't resume from failure point

### Issue 3: BERTopic Limitations
**Problems:**
1. **Dataset Too Small** - 133 papers insufficient for 30 topics
2. **Only 1 Real Topic Found** - All papers lumped into one cluster
3. **Theme Assignment Lost** - Original theme tags from collection ignored

---

## 🎯 **PROPOSED SOLUTIONS**

### **Solution 1: Increase Paper Collection (Target: 500+ papers)**

#### A. Relax Relevance Threshold
**Current:** `min_relevance = 0.1` (10%)  
**Proposed:** `min_relevance = 0.05` (5%)  
**Impact:** +20-30 more papers

```python
# config/settings.py
MIN_RELEVANCE_SCORE = 0.05  # Was 0.1
```

#### B. Reduce Deduplication Aggressiveness
**Current:** Removes 29.3% of papers  
**Proposed:** Only remove exact DOI duplicates, keep title variations

```python
# src/theme_based_collector.py
def deduplicate_papers(self, df: pd.DataFrame) -> pd.DataFrame:
    """Less aggressive deduplication - only exact DOI matches"""
    # Remove only exact DOI duplicates
    df_dedup = df.drop_duplicates(subset=['doi'], keep='first')
    
    # Keep papers with different DOIs even if titles similar
    return df_dedup
```

**Impact:** Retain ~30-40 more papers

#### C. Increase Papers Per Theme
**Current:** No limit (but sparse results)  
**Proposed:** Set `max_per_theme = 100` for full collection

```python
# run_full_analysis.py
max_per_theme = 100  # Was None (unlimited but got few results)
```

**Impact:** More targeted collection per theme

#### D. Expand Date Range
**Current:** 2020-01-01 to 2024-12-31 (5 years)  
**Proposed:** 2018-01-01 to 2024-12-31 (7 years)

```python
# config/settings.py
START_DATE = "2018-01-01"  # Was 2020-01-01
```

**Impact:** +100-150 more papers

#### E. Broaden Keyword Matching
**Current:** Strict concept + keyword matching  
**Proposed:** Add more synonyms and related terms

```python
# config/themes.py
"Defense_Security": {
    "keywords": [
        # Add more terms
        "defense", "defence", "military", "security", "national security",
        "defense technology", "military technology", "strategic defense",
        "homeland security", "border security", "critical infrastructure protection"
    ],
    "concepts": [
        # Add more OpenAlex concepts
        "Military science", "National security", "Homeland security",
        "Defense industry", "Military technology"
    ]
}
```

**Impact:** +50-100 more papers for sparse themes

---

### **Solution 2: Implement Checkpointing System**

#### A. Theme-Level Checkpoints
Save progress after each theme completes:

```python
# src/theme_based_collector.py
import json
from pathlib import Path

CHECKPOINT_DIR = Path("data/checkpoints")
CHECKPOINT_FILE = CHECKPOINT_DIR / "collection_checkpoint.json"

def save_checkpoint(self, completed_themes: list, papers_df: pd.DataFrame):
    """Save collection checkpoint"""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    
    checkpoint = {
        'timestamp': datetime.now().isoformat(),
        'completed_themes': completed_themes,
        'total_papers': len(papers_df),
        'papers_file': 'data/checkpoints/papers_partial.csv'
    }
    
    # Save checkpoint metadata
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)
    
    # Save partial papers
    papers_df.to_csv(checkpoint['papers_file'], index=False)
    logger.info(f"✅ Checkpoint saved: {len(completed_themes)} themes, {len(papers_df)} papers")

def load_checkpoint(self):
    """Load existing checkpoint if available"""
    if not CHECKPOINT_FILE.exists():
        return None, []
    
    with open(CHECKPOINT_FILE, 'r') as f:
        checkpoint = json.load(f)
    
    papers_df = pd.read_csv(checkpoint['papers_file'])
    logger.info(f"📂 Loaded checkpoint: {len(checkpoint['completed_themes'])} themes completed")
    
    return papers_df, checkpoint['completed_themes']
```

#### B. Resume from Checkpoint
```python
def fetch_all_themes(self, universities, max_per_theme=None, priority_only=False, min_relevance=0.1):
    """Fetch papers with checkpoint support"""
    
    # Try to load checkpoint
    existing_papers, completed_themes = self.load_checkpoint()
    
    if existing_papers is not None:
        logger.info(f"🔄 Resuming from checkpoint ({len(completed_themes)} themes done)")
        all_papers = [existing_papers]
    else:
        all_papers = []
        completed_themes = []
    
    # Get remaining themes
    themes_to_process = [t for t in theme_list if t not in completed_themes]
    
    for theme in themes_to_process:
        try:
            papers = self.fetch_papers_for_theme(theme, universities, max_per_theme)
            all_papers.append(papers)
            completed_themes.append(theme)
            
            # Save checkpoint after each theme
            combined_df = pd.concat(all_papers, ignore_index=True)
            self.save_checkpoint(completed_themes, combined_df)
            
        except Exception as e:
            logger.error(f"❌ Failed on theme {theme}: {e}")
            # Checkpoint already saved, can resume later
            raise
    
    return pd.concat(all_papers, ignore_index=True)
```

**Impact:** Can resume after interruption, no lost progress

---

### **Solution 3: Cache Institution IDs**

**Problem:** Currently resolves 44 universities × 9 themes = 396 times (wasteful!)

```python
# src/theme_based_collector.py
INSTITUTION_CACHE_FILE = Path("data/cache/institution_ids.json")

def load_institution_cache(self):
    """Load cached institution IDs"""
    if not INSTITUTION_CACHE_FILE.exists():
        return {}
    
    with open(INSTITUTION_CACHE_FILE, 'r') as f:
        return json.load(f)

def save_institution_cache(self, cache: dict):
    """Save institution ID cache"""
    INSTITUTION_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INSTITUTION_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def resolve_institution_ids(self, universities: Dict[str, str]) -> Dict[str, str]:
    """Resolve with caching"""
    cache = self.load_institution_cache()
    resolved = {}
    new_resolutions = False
    
    for uni_name, placeholder_id in universities.items():
        # Check cache first
        if uni_name in cache:
            resolved[uni_name] = cache[uni_name]
            logger.debug(f"[CACHE HIT] {uni_name} -> {cache[uni_name]}")
            continue
        
        # Resolve and cache
        openalex_id = self._resolve_single_institution(uni_name)
        if openalex_id:
            resolved[uni_name] = openalex_id
            cache[uni_name] = openalex_id
            new_resolutions = True
    
    # Save cache if new resolutions
    if new_resolutions:
        self.save_institution_cache(cache)
    
    return resolved
```

**Impact:** 
- First run: 396 API calls
- Subsequent runs: 0 API calls (instant!)
- Saves ~10-15 minutes per collection

---

### **Solution 4: Preserve Original Theme Tags**

**Problem:** BERTopic overwrites original theme assignments from collection

```python
# run_full_analysis.py - Step 3
def step3_topic_modeling():
    # ... existing code ...
    
    # PRESERVE original theme from collection
    metadata['original_theme'] = metadata['theme']  # Save before BERTopic
    metadata['topic_id'] = topics
    metadata['topic_probability'] = [p.max() if len(p) > 0 else 0 for p in probs]
    
    # Use original theme as fallback if BERTopic confidence is low
    metadata['final_theme'] = metadata.apply(
        lambda row: row['original_theme'] if row['topic_probability'] < 0.3 
        else row['bertopic_theme'], 
        axis=1
    )
```

**Impact:** Retain theme diversity, avoid all papers in 2 themes

---

### **Solution 5: Parallel Theme Collection**

**Current:** Sequential (9 themes × 7 min = 63 min)  
**Proposed:** Parallel (9 themes / 3 workers = 21 min)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_all_themes_parallel(self, universities, max_per_theme=None, max_workers=3):
    """Fetch themes in parallel"""
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all theme collection tasks
        future_to_theme = {
            executor.submit(
                self.fetch_papers_for_theme, 
                theme, 
                universities, 
                max_per_theme
            ): theme 
            for theme in BABCOCK_THEMES.keys()
        }
        
        all_papers = []
        for future in as_completed(future_to_theme):
            theme = future_to_theme[future]
            try:
                papers = future.result()
                all_papers.append(papers)
                logger.info(f"✅ Completed {theme}: {len(papers)} papers")
            except Exception as e:
                logger.error(f"❌ Failed {theme}: {e}")
        
        return pd.concat(all_papers, ignore_index=True)
```

**Impact:** 3x faster collection (63 min → 21 min)

---

### **Solution 6: Smarter BERTopic Configuration**

#### A. Use Original Themes as Seed Topics
```python
# src/topic_analyzer.py
from bertopic.representation import KeyBERTInspired

def create_bertopic_model_with_seeds(self, seed_topics: dict):
    """Initialize BERTopic with seed topics from collection"""
    
    # Use seed topics to guide clustering
    seed_topic_list = [
        [kw for kw in theme_data['keywords'][:10]]
        for theme_data in seed_topics.values()
    ]
    
    representation_model = KeyBERTInspired()
    
    self.topic_model = BERTopic(
        embedding_model=embedding_model,
        representation_model=representation_model,
        seed_topic_list=seed_topic_list,  # Guide with collection themes
        min_topic_size=self.min_topic_size,
        nr_topics=len(seed_topics),  # Match number of collection themes
        calculate_probabilities=True
    )
```

#### B. Increase Min Topic Size for Small Datasets
```python
# Adaptive min_topic_size based on dataset size
def get_adaptive_min_topic_size(n_documents: int) -> int:
    if n_documents < 200:
        return max(3, n_documents // 40)  # ~3-5 for 133 papers
    elif n_documents < 500:
        return max(5, n_documents // 50)
    else:
        return 10
```

---

## 📊 **EXPECTED IMPROVEMENTS**

### Before Improvements:
- **Papers Collected:** 140
- **Papers After Processing:** 133
- **Themes with Papers:** 2 (AI/ML, Energy)
- **Collection Time:** ~60 min
- **Checkpoint Support:** ❌ No
- **Institution Cache:** ❌ No

### After Improvements:
- **Papers Collected:** 400-500 (3-4x increase)
- **Papers After Processing:** 350-450
- **Themes with Papers:** 7-9 (all themes)
- **Collection Time:** ~25 min (2.4x faster with parallel + cache)
- **Checkpoint Support:** ✅ Yes
- **Institution Cache:** ✅ Yes

---

## 🚀 **IMPLEMENTATION PRIORITY**

### **Phase 1: Quick Wins (Implement Today)**
1. ✅ Relax relevance threshold (0.1 → 0.05)
2. ✅ Expand date range (2020 → 2018)
3. ✅ Increase max_per_theme to 100
4. ✅ Less aggressive deduplication

**Expected Impact:** +150-200 papers

### **Phase 2: Efficiency (Implement Tomorrow)**
1. ✅ Institution ID caching
2. ✅ Theme-level checkpointing
3. ✅ Preserve original theme tags

**Expected Impact:** 3x faster, resume capability

### **Phase 3: Advanced (Implement This Week)**
1. ✅ Parallel theme collection
2. ✅ Smarter BERTopic with seed topics
3. ✅ Broader keyword matching

**Expected Impact:** 5x faster, better theme coverage

---

## 📝 **NEXT STEPS**

1. **Implement Phase 1 changes** (30 min)
2. **Re-run collection** (25 min with improvements)
3. **Verify results** (check theme distribution)
4. **Implement Phase 2** (2 hours)
5. **Test checkpoint recovery** (simulate interruption)
6. **Implement Phase 3** (4 hours)

---

## ✅ **SUCCESS METRICS**

- [ ] Collect 400+ papers
- [ ] All 9 themes have ≥20 papers each
- [ ] Collection completes in <30 min
- [ ] Checkpoint recovery works
- [ ] Institution cache reduces API calls by 95%
- [ ] BERTopic finds 8-12 meaningful topics
