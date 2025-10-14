# AI/ML Low Paper Count - ROOT CAUSE & FIX

## Problem
AI_Machine_Learning theme was getting 0-24 papers while other themes got thousands.

## Investigation

### Test 1: Check if keywords work
✅ **Result**: Query works fine! OpenAlex finds 328-1644 AI/ML papers from 3 universities alone.

### Test 2: Check for keyword overlaps
✅ **Result**: No keyword overlaps between AI/ML and other themes.

### Test 3: Check multi-word search terms
✅ **Result**: Multi-word terms ("machine learning", "deep learning") work correctly.

## ROOT CAUSE FOUND! 🎯

**The problem is FETCH ORDER + DEDUPLICATION**

### How Collection Works:
1. Themes are fetched **sequentially** (one after another)
2. Each paper is tagged with the **first theme** it's found under
3. Later, **deduplication removes papers already tagged** with other themes

### The Issue:
```
Fetch Order (before fix):
1. Defense_Security     → Captures "AI for threat detection"
2. Autonomous_Systems   → Captures "ML for autonomous vehicles"
3. Cybersecurity        → Captures "AI for intrusion detection"
4. Marine_Naval         → Captures "ML for underwater navigation"
5. AI_Machine_Learning  → Gets NOTHING LEFT! (already captured above)
```

### Why AI/ML Gets Nothing:
- **Defense papers** mentioning "machine learning for surveillance" → Tagged as Defense
- **Autonomous papers** with "neural networks for robotics" → Tagged as Autonomous
- **Cybersecurity papers** about "AI threat detection" → Tagged as Cybersecurity
- **By the time AI/ML fetch happens**, all AI/ML papers are already tagged!

## THE FIX ✅

### Changed Fetch Order:
```python
# src/theme_based_collector.py - fetch_all_themes()

# IMPORTANT: Fetch AI/ML first to avoid it being captured by other themes
if 'AI_Machine_Learning' in themes_to_fetch:
    themes_to_fetch.remove('AI_Machine_Learning')
    themes_to_fetch.insert(0, 'AI_Machine_Learning')
```

### New Fetch Order:
```
1. AI_Machine_Learning  → Captures core AI/ML papers FIRST ✅
2. Defense_Security     → Gets defense papers (minus AI/ML ones)
3. Autonomous_Systems   → Gets robotics papers (minus AI/ML ones)
4. Cybersecurity        → Gets security papers (minus AI/ML ones)
5. Marine_Naval         → Gets marine papers (minus AI/ML ones)
... etc
```

## Expected Results After Fix

### Before:
- AI_Machine_Learning: **24 papers** ❌
- Autonomous_Systems: 2,654 papers (includes many AI/ML papers)
- Defense_Security: 4,649 papers (includes many AI/ML papers)

### After (Expected):
- **AI_Machine_Learning: 1,000-2,000 papers** ✅
- Autonomous_Systems: 1,500-2,000 papers (reduced, as AI/ML papers moved out)
- Defense_Security: 4,000-4,500 papers (reduced, as AI/ML papers moved out)

## Additional Improvements

### Expanded AI/ML Keywords (from 18 → 92 keywords):
Added:
- **Neural architectures**: ResNet, VGG, AlexNet, U-Net, attention mechanism
- **ML tools**: TensorFlow, PyTorch, Keras, scikit-learn, OpenCV, YOLO
- **ML techniques**: ensemble learning, bagging, boosting, k-means, cross-validation
- **Edge AI**: model compression, quantization, knowledge distillation, pruning
- **Applications**: facial recognition, pose estimation, OCR, chatbot, time series forecasting

## Verification

Run the analysis again and check:
```bash
python run_full_analysis.py 3
```

Check logs for:
- ✅ AI_Machine_Learning fetched FIRST
- ✅ AI_Machine_Learning shows 1000-2000+ papers collected
- ✅ Other themes still get good numbers but slightly reduced

## Why This Matters

**Proper theme categorization** ensures:
- ✅ AI/ML research is properly tracked as its own strategic area
- ✅ Strategic priorities calculated correctly for AI/ML theme
- ✅ Trend analysis shows AI/ML growth independently
- ✅ Dashboard displays balanced theme distribution

Without this fix, AI/ML was being **hidden within other themes**, making it impossible to track Babcock's AI/ML strategic priorities!
