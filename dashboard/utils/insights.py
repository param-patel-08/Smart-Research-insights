"""
Insight generation and topic analysis utilities.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def generate_insights(df, trends, mapping):
    """Generate actionable insights from the data"""
    insights = []
    
    # 1. Emerging Sub-Themes (fastest growing)
    sub_theme_growth = df.groupby(['sub_theme', df['date'].dt.year]).size().unstack(fill_value=0)
    if len(sub_theme_growth.columns) >= 2:
        recent_year = sub_theme_growth.columns[-1]
        prev_year = sub_theme_growth.columns[-2]
        growth_rates = ((sub_theme_growth[recent_year] - sub_theme_growth[prev_year]) / 
                       (sub_theme_growth[prev_year] + 1) * 100)
        top_emerging = growth_rates.nlargest(3)
        
        if len(top_emerging) > 0 and top_emerging.iloc[0] > 20:
            insights.append({
                "type": "emerging",
                "icon": "",
                "title": "Rapid Growth Detected",
                "message": f"{top_emerging.index[0]} showing {top_emerging.iloc[0]:.0f}% growth",
                "detail": f"From {int(sub_theme_growth.loc[top_emerging.index[0], prev_year])} papers ({prev_year}) to {int(sub_theme_growth.loc[top_emerging.index[0], recent_year])} ({recent_year})"
            })
    
    # 2. Collaboration Opportunities (low research volume but high strategic priority)
    theme_counts = df.groupby('theme').size()
    high_priority_themes = [p['theme'] for p in trends.get('strategic_priorities', [])[:3]]
    for theme in high_priority_themes:
        if theme in theme_counts and theme_counts[theme] < 1500:
            insights.append({
                "type": "opportunity",
                "icon": "",
                "title": "Collaboration Gap",
                "message": f"{theme.replace('_', ' ')} is high priority but underrepresented",
                "detail": f"Only {theme_counts[theme]:,} papers vs {theme_counts.max():,} in leading theme"
            })
            break
    
    # 3. Research Concentration
    top_unis = df['university'].value_counts()
    concentration = (top_unis.head(3).sum() / len(df) * 100)
    if concentration > 40:
        insights.append({
            "type": "concentration",
            "icon": "",
            "title": "Research Concentration",
            "message": f"Top 3 universities produce {concentration:.0f}% of research",
            "detail": f"{top_unis.index[0]} leads with {top_unis.iloc[0]:,} papers"
        })
    
    # 4. Quality vs Quantity
    if 'quality_score' in df.columns:
        high_quality = df[df['quality_score'] > 70]
        quality_by_theme = high_quality.groupby('theme').size().sort_values(ascending=False)
        if len(quality_by_theme) > 0:
            top_quality_theme = quality_by_theme.index[0]
            quality_pct = (quality_by_theme.iloc[0] / df[df['theme']==top_quality_theme].shape[0] * 100)
            insights.append({
                "type": "quality",
                "icon": "",
                "title": "Quality Leader",
                "message": f"{top_quality_theme.replace('_', ' ')} has highest quality research",
                "detail": f"{quality_pct:.0f}% of papers score >70 quality"
            })
    
    # 5. Temporal Trends
    recent_6m = df[df['date'] >= (df['date'].max() - pd.Timedelta(days=180))]
    recent_growth = len(recent_6m) / (len(df) - len(recent_6m)) * 100 if len(df) > len(recent_6m) else 0
    if recent_growth > 15:
        insights.append({
            "type": "trend",
            "icon": "",
            "title": "Accelerating Research",
            "message": f"Last 6 months show {recent_growth:.0f}% increase",
            "detail": f"{len(recent_6m):,} recent papers indicate strong momentum"
        })
    
    # 6. Cross-theme opportunities
    if 'all_scores' in str(mapping.values()):
        # Find topics that span multiple themes (good for collaboration)
        multi_theme_topics = []
        for topic_id, data in mapping.items():
            all_scores = data.get('all_scores', {})
            high_scores = [t for t, s in all_scores.items() if s > 0.3]
            if len(high_scores) > 1:
                multi_theme_topics.append(topic_id)
        
        if len(multi_theme_topics) > 5:
            insights.append({
                "type": "collaboration",
                "icon": "🤝",
                "title": "Cross-Theme Potential",
                "message": f"{len(multi_theme_topics)} topics span multiple themes",
                "detail": "Strong opportunity for interdisciplinary collaboration"
            })
    
    return insights[:5]  # Return top 5 insights


def filter_noisy_keywords(keywords):
    """Remove noisy/generic keywords"""
    noise_words = {
        'google', 'scholar', 'researchgate', 'pubmed', 'arxiv',
        'et', 'al', 'doi', 'http', 'https', 'www',
        'paper', 'study', 'research', 'analysis', 'approach',
        'method', 'results', 'data', 'using', 'based',
        'review', 'systematic', 'meta',
        'journal', 'conference', 'proceedings', 'article'
    }
    
    filtered = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in noise_words and len(kw) > 2:
            if not any(x in kw_lower for x in ['http', 'www', '.com', '.org']):
                filtered.append(kw)
    
    return filtered[:8]


def generate_topic_label_gpt(keywords, theme, sub_theme, paper_count, growth_rate):
    """Generate meaningful topic label using GPT"""
    import openai
    import os
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        # Fallback to cleaned keywords
        clean_kw = filter_noisy_keywords(keywords)
        if len(clean_kw) >= 2:
            return f"{theme.replace('_', ' ')}: {' & '.join(clean_kw[:2])}"
        return f"Topic in {theme.replace('_', ' ')}"
    
    try:
        openai.api_key = api_key
        
        clean_keywords = filter_noisy_keywords(keywords)
        if len(clean_keywords) < 3:
            clean_keywords = keywords[:8]
        
        keywords_str = ", ".join(clean_keywords[:8])
        domain = theme.replace('_', ' ').title()
        sub_context = f"\nSub-area: {sub_theme.replace('_', ' ')}" if sub_theme else ""
        
        prompt = f"""You are a research analyst identifying emerging topics.

Domain: {domain}{sub_context}
Keywords: {keywords_str}
Papers: {paper_count}
Growth: {growth_rate:.0f}%

Create a SHORT research topic label (2-4 words MAXIMUM) that:
- Describes the SPECIFIC focus
- Uses technical terms
- Is concise and memorable

Good examples:
- "Medical Image AI"
- "Blockchain Security"
- "Edge IoT"
- "Quantum Computing"

Generate ONLY the label (2-4 words MAX), no quotes."""

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You create SHORT (2-4 word) research labels. Never list keywords."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=30
        )
        
        label = response.choices[0].message.content.strip().strip('"').strip("'").strip('`')
        
        # Remove prefixes
        for prefix in ['Topic:', 'Label:', 'Research Topic:', 'Emerging Topic:']:
            if label.startswith(prefix):
                label = label[len(prefix):].strip()
        
        return label if len(label.split()) >= 3 else f"{domain}: {' & '.join(clean_keywords[:2])}"
        
    except Exception as e:
        # Fallback
        clean_kw = filter_noisy_keywords(keywords)
        if len(clean_kw) >= 2:
            return f"{theme.replace('_', ' ')}: {' & '.join(clean_kw[:2])}"
        return f"Topic in {theme.replace('_', ' ')}"


def create_emerging_topics_bubble(df, mapping, top_n=20):
    """
    Create bubble chart showing emerging topics with GPT-generated labels
    X-axis: Recency score (how recent)
    Y-axis: Growth rate (how fast growing)
    Size: Paper volume
    Color: Theme
    """
    # Calculate emergingness metrics for each topic
    emerging_data = []
    
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    latest_date = df_copy['date'].max()
    
    for topic_id in df_copy['topic_id'].unique():
        if topic_id == -1:  # Skip outliers
            continue
        
        topic_papers = df_copy[df_copy['topic_id'] == topic_id]
        
        if len(topic_papers) < 5:  # Skip small topics
            continue
        
        # Calculate recency score
        topic_papers['months_old'] = (latest_date - topic_papers['date']).dt.days / 30
        recency_score = np.exp(-topic_papers['months_old'].mean() / 12)  # Exponential decay
        
        # Calculate growth rate
        topic_papers['quarter'] = topic_papers['date'].dt.to_period('Q')
        quarterly_counts = topic_papers.groupby('quarter').size().sort_index()
        
        if len(quarterly_counts) >= 4:
            recent_avg = quarterly_counts.iloc[-2:].mean()
            older_avg = quarterly_counts.iloc[-4:-2].mean()
            growth_rate = ((recent_avg - older_avg) / max(older_avg, 1)) * 100
        elif len(quarterly_counts) >= 2:
            growth_rate = ((quarterly_counts.iloc[-1] - quarterly_counts.iloc[0]) / max(quarterly_counts.iloc[0], 1)) * 100
        else:
            growth_rate = 0
        
        # Get theme and keywords
        topic_id_str = str(topic_id)
        theme = topic_papers['theme'].iloc[0] if 'theme' in topic_papers.columns else 'Unknown'
        sub_theme = topic_papers['sub_theme'].iloc[0] if 'sub_theme' in topic_papers.columns else None
        
        keywords = []
        if topic_id_str in mapping:
            keywords = mapping[topic_id_str].get('keywords', [])[:10]
        
        emerging_data.append({
            'topic_id': topic_id,
            'keywords_list': keywords,
            'theme': theme,
            'sub_theme': sub_theme,
            'recency_score': recency_score * 100,  # Convert to percentage
            'growth_rate': growth_rate,
            'paper_count': len(topic_papers),
            'avg_citations': topic_papers['citations'].mean() if 'citations' in topic_papers.columns else 0,
            'keywords': ', '.join(filter_noisy_keywords(keywords)[:5])
        })
    
    emerging_df = pd.DataFrame(emerging_data)
    
    # Calculate emergingness score and filter top N
    emerging_df['emergingness'] = (
        0.4 * (emerging_df['recency_score'] / 100) +
        0.4 * ((emerging_df['growth_rate'] + 100) / 200) +  # Normalize growth
        0.2 * (emerging_df['paper_count'] / emerging_df['paper_count'].max())
    )
    
    emerging_df = emerging_df.nlargest(top_n, 'emergingness')
    
    # Generate GPT labels for top topics
    with st.spinner('Generating AI-powered topic labels...'):
        labels = []
        for _, row in emerging_df.iterrows():
            label = generate_topic_label_gpt(
                keywords=row['keywords_list'],
                theme=row['theme'],
                sub_theme=row['sub_theme'],
                paper_count=row['paper_count'],
                growth_rate=row['growth_rate']
            )
            labels.append(label)
        emerging_df['topic_label'] = labels
    
    # Create bubble chart
    fig = px.scatter(
        emerging_df,
        x='recency_score',
        y='growth_rate',
        size='paper_count',
        color='theme',
        hover_name='topic_label',
        hover_data={
            'recency_score': ':.1f',
            'growth_rate': ':.1f',
            'paper_count': True,
            'avg_citations': ':.1f',
            'theme': False,
            'keywords': True
        },
        title=f"Top {top_n} Emerging Research Topics",
        labels={
            'recency_score': 'Recency Score (% papers in last 12 months)',
            'growth_rate': 'Growth Rate (%)',
            'paper_count': 'Papers',
            'theme': 'Theme'
        },
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    # Add quadrant lines
    median_recency = emerging_df['recency_score'].median()
    median_growth = emerging_df['growth_rate'].median()
    
    fig.add_hline(y=median_growth, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=median_recency, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Add annotations for quadrants
    max_recency = emerging_df['recency_score'].max()
    max_growth = emerging_df['growth_rate'].max()
    min_growth = emerging_df['growth_rate'].min()
    
    fig.add_annotation(
        x=max_recency * 0.85,
        y=max_growth * 0.85,
        text="Hot Topics<br>(Recent + Growing)",
        showarrow=False,
        font=dict(size=10, color="#3b82f6"),
        opacity=0.7
    )
    
    fig.add_annotation(
        x=median_recency * 0.5,
        y=max_growth * 0.85,
        text="Momentum<br>(Growing Fast)",
        showarrow=False,
        font=dict(size=10, color="blue"),
        opacity=0.7
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        hovermode='closest'
    )
    
    return fig, emerging_df
