# 🔥 Emerging Topics Detection - Quick Guide

## What's Been Added

### 1. **New Script: `src/emerging_topics_detector.py`**
Analyzes topics and calculates "emergingness" scores based on:
- **Recency** (40%): How recent are the papers?
- **Growth** (40%): How fast is the topic growing?
- **Volume** (20%): How many papers?

### 2. **New Dashboard Tab: "🔥 Emerging Topics"**
Interactive visualization showing:
- **Bubble Chart**: X=Recency, Y=Growth, Size=Papers, Color=Theme
- **Top Topics Table**: Ranked list with all metrics
- **Strategic Insights**: Hottest topics, momentum leaders, recent surges
- **Theme Breakdown**: Which themes have most emerging topics

## How to Use

### Option 1: View in Dashboard (Easiest)
```powershell
streamlit run dashboard/app.py
```
- Click on "🔥 Emerging Topics" tab
- Adjust slider to show 10-30 topics
- Hover over bubbles to see details
- Look for topics in top-right quadrant (🌟 hot topics)

### Option 2: Run Script Directly
```powershell
python src/emerging_topics_detector.py
```
- Generates `data/processed/emerging_topics.json`
- Prints top 20 emerging topics to console

### Option 3: Use with ChatGPT API (Optional)
1. Add to `.env`:
```
OPENAI_API_KEY=your-key-here
```

2. Run script:
```powershell
python src/emerging_topics_detector.py
```
- Script will use GPT-4o-mini to generate human-readable labels
- Falls back to keywords if no API key

## Understanding the Bubble Chart

### Quadrants
- **Top-Right (🌟)**: Hot topics - Recent AND growing fast → **INVEST HERE**
- **Top-Left (📈)**: Momentum - Older but growing fast → Watch for sustainability
- **Bottom-Right (🔥)**: Recent surges - New but not yet proven → Monitor closely
- **Bottom-Left**: Declining - May be losing relevance

### Bubble Properties
- **Size**: Bigger = More papers
- **Color**: Different themes
- **Position**: Top-right = Most emerging

## What You Get

### Metrics for Each Topic:
- **Emergingness Score**: Overall score (0-1, higher = more emerging)
- **Recency Score**: % of papers in last 12 months
- **Growth Rate**: Quarterly growth percentage
- **Paper Count**: Total papers in topic
- **Avg Citations**: Impact measurement
- **Keywords**: Top 5 BERTopic keywords
- **Theme & Sub-Theme**: Classification

### Strategic Insights:
- **Hottest Topics**: Best investment opportunities
- **Momentum Leaders**: Fastest growing
- **Recent Surges**: Latest activity
- **Theme Breakdown**: Where emerging research is concentrated

## My Recommendation: Keep It Simple!

✅ **You DON'T need to:**
- Fine-tune keywords (BERTopic already did this!)
- Train new ML models
- Do complex preprocessing

✅ **You DO get:**
- Automatic keyword extraction from BERTopic
- Smart emergingness calculation
- Interactive bubble chart (already styled by theme!)
- Optional GPT labels for readability

## API Cost (if using GPT)
- Model: GPT-4o-mini (~$0.15 per 1M tokens)
- Cost per topic: ~$0.0001 (basically free!)
- For 20 topics: ~$0.002 total

## Next Steps

1. **View Dashboard**: See the visualization
2. **Identify Hot Topics**: Focus on top-right quadrant
3. **Optional**: Add OpenAI API key for better labels
4. **Share**: Export bubble chart for presentations

## Files Created
- `src/emerging_topics_detector.py` - Detection script
- `dashboard/app.py` - Updated with new tab (line ~1410-1550)
- `data/processed/emerging_topics.json` - Output file (when script runs)

That's it! No complex setup needed. 🎉
