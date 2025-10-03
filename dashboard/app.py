"""
Babcock Research Trends - Streamlit Dashboard
Interactive dashboard for exploring research trends
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.themes import BABCOCK_THEMES

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="Babcock Research Trends",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4788;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c5aa0;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4788;
    }
    .priority-high {
        background-color: #ffebee;
        border-left-color: #d32f2f;
    }
    .priority-medium {
        background-color: #fff3e0;
        border-left-color: #f57c00;
    }
    .priority-low {
        background-color: #e8f5e9;
        border-left-color: #388e3c;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== LOAD DATA ====================

@st.cache_data
def load_data():
    """Load all analysis data"""
    try:
        papers_df = pd.read_csv('data/processed/papers_with_topics.csv')
        papers_df['date'] = pd.to_datetime(papers_df['date'])
        
        with open('data/processed/trend_analysis.json', 'r') as f:
            trends = json.load(f)
        
        with open('models/topic_theme_mapping.json', 'r') as f:
            mapping = json.load(f)
        
        return papers_df, trends, mapping
    except FileNotFoundError as e:
        st.error(f"⚠️ Data files not found! Please run the analysis first: `python run_full_analysis.py`")
        st.stop()

# Load data
papers_df, trends, mapping = load_data()

# Add theme to papers
papers_df['theme'] = papers_df['topic_id'].astype(str).map(
    lambda tid: mapping.get(tid, {}).get('theme', 'Other')
)
papers_df['quarter'] = papers_df['date'].dt.to_period('Q')

# ==================== SIDEBAR ====================

st.sidebar.image("https://via.placeholder.com/300x80/1f4788/ffffff?text=BABCOCK", use_container_width=True)
st.sidebar.title("🔬 Research Trends")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Overview", "🎯 Theme Analysis", "⚡ Emerging Topics", "🏛️ Universities", "📈 Trends Over Time"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 Analysis Period")
st.sidebar.info(f"{papers_df['date'].min().strftime('%b %Y')} - {papers_df['date'].max().strftime('%b %Y')}")

st.sidebar.markdown("### 📊 Quick Stats")
st.sidebar.metric("Total Papers", f"{len(papers_df):,}")
st.sidebar.metric("Topics Found", len(mapping))
st.sidebar.metric("Universities", papers_df['university'].nunique())

# ==================== OVERVIEW PAGE ====================

if page == "📊 Overview":
    st.markdown('<p class="main-header">🔬 Babcock Research Trends Dashboard</p>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Australasian Research Intelligence System
    Automated tracking of emerging research trends across 24 universities in Australia and New Zealand,
    mapped to Babcock's 9 strategic technology themes.
    """)
    
    st.markdown("---")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📄 Papers Analyzed",
            f"{len(papers_df):,}",
            help="Total papers collected and analyzed"
        )
    
    with col2:
        st.metric(
            "🔬 Topics Discovered",
            len(mapping),
            help="Research topics identified by BERTopic"
        )
    
    with col3:
        st.metric(
            "🏛️ Universities",
            papers_df['university'].nunique(),
            help="Australian and New Zealand universities tracked"
        )
    
    with col4:
        avg_growth = sum(p['growth_rate'] for p in trends['strategic_priorities']) / len(trends['strategic_priorities'])
        st.metric(
            "📈 Avg Growth Rate",
            f"{avg_growth*100:+.1f}%",
            help="Average quarterly growth across all themes"
        )
    
    st.markdown("---")
    
    # Strategic Priorities
    st.markdown('<p class="sub-header">🎯 Strategic Theme Priorities</p>', unsafe_allow_html=True)
    
    priorities = trends['strategic_priorities']
    
    # Create two columns for priorities
    col1, col2 = st.columns(2)
    
    for i, priority in enumerate(priorities):
        theme = priority['theme']
        category = priority['category']
        growth = priority['growth_rate']
        papers = priority['total_papers']
        
        # Choose column
        col = col1 if i % 2 == 0 else col2
        
        with col:
            # Style based on priority
            priority_class = f"priority-{category.lower()}"
            
            # Growth indicator
            if growth > 0.5:
                indicator = "🚀 RAPIDLY GROWING"
            elif growth > 0.2:
                indicator = "📈 GROWING"
            elif growth > -0.1:
                indicator = "➡️ STABLE"
            else:
                indicator = "📉 DECLINING"
            
            st.markdown(f"""
            <div class="metric-card {priority_class}">
                <h4>{theme.replace('_', ' ').title()}</h4>
                <p><strong>{indicator}</strong> ({category})</p>
                <p>Growth: <strong>{growth*100:+.1f}%</strong> | Papers: <strong>{papers:,}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Theme Distribution Chart
    st.markdown('<p class="sub-header">📊 Research Distribution by Theme</p>', unsafe_allow_html=True)
    
    theme_counts = papers_df['theme'].value_counts()
    theme_counts = theme_counts[theme_counts.index != 'Other']
    
    fig = px.bar(
        x=theme_counts.values,
        y=[t.replace('_', ' ').title() for t in theme_counts.index],
        orientation='h',
        title='Papers per Strategic Theme',
        labels={'x': 'Number of Papers', 'y': 'Theme'},
        color=theme_counts.values,
        color_continuous_scale='Blues'
    )
    fig.update_layout(height=500, showlegend=False)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Quarterly Trend
    st.markdown('<p class="sub-header">📈 Research Output Over Time</p>', unsafe_allow_html=True)
    
    quarterly = papers_df.groupby(['quarter', 'theme']).size().reset_index(name='count')
    quarterly['quarter'] = quarterly['quarter'].astype(str)
    quarterly['theme'] = quarterly['theme'].str.replace('_', ' ').str.title()
    
    fig = px.line(
        quarterly,
        x='quarter',
        y='count',
        color='theme',
        title='Quarterly Research Output by Theme',
        labels={'count': 'Number of Papers', 'quarter': 'Quarter', 'theme': 'Theme'},
        markers=True
    )
    fig.update_layout(height=500, hovermode='x unified')
    
    st.plotly_chart(fig, use_container_width=True)

# ==================== THEME ANALYSIS PAGE ====================

elif page == "🎯 Theme Analysis":
    st.markdown('<p class="main-header">🎯 Theme Analysis</p>', unsafe_allow_html=True)
    
    # Theme selector
    theme_names = [t.replace('_', ' ').title() for t in BABCOCK_THEMES.keys()]
    selected_theme_display = st.selectbox("Select Theme", theme_names)
    selected_theme = selected_theme_display.replace(' ', '_')
    
    # Filter data for selected theme
    theme_papers = papers_df[papers_df['theme'] == selected_theme]
    
    if len(theme_papers) == 0:
        st.warning(f"No papers found for theme: {selected_theme_display}")
        st.stop()
    
    st.markdown("---")
    
    # Theme metrics
    col1, col2, col3, col4 = st.columns(4)
    
    theme_trend = trends['theme_trends'].get(selected_theme, {})
    growth_rate = theme_trend.get('growth_rate', 0)
    
    with col1:
        st.metric("Total Papers", f"{len(theme_papers):,}")
    
    with col2:
        st.metric("Growth Rate", f"{growth_rate*100:+.1f}%")
    
    with col3:
        st.metric("Sub-Topics", theme_papers['topic_id'].nunique())
    
    with col4:
        st.metric("Universities", theme_papers['university'].nunique())
    
    st.markdown("---")
    
    # Two columns layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Temporal trend
        st.subheader("📈 Trend Over Time")
        
        quarterly_theme = theme_papers.groupby('quarter').size().reset_index(name='count')
        quarterly_theme['quarter'] = quarterly_theme['quarter'].astype(str)
        
        fig = px.bar(
            quarterly_theme,
            x='quarter',
            y='count',
            title=f'{selected_theme_display} - Quarterly Output',
            labels={'count': 'Papers', 'quarter': 'Quarter'},
            color='count',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top universities
        st.subheader("🏛️ Leading Universities")
        
        uni_counts = theme_papers['university'].value_counts().head(10)
        
        fig = px.bar(
            x=uni_counts.values,
            y=uni_counts.index,
            orientation='h',
            title=f'Top 10 Universities in {selected_theme_display}',
            labels={'x': 'Papers', 'y': 'University'},
            color=uni_counts.values,
            color_continuous_scale='Greens'
        )
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Top Topics in Theme
    st.subheader("🔍 Top Research Topics")
    
    topic_counts = theme_papers['topic_id'].value_counts().head(10)
    
    for topic_id in topic_counts.index:
        if str(topic_id) in mapping:
            topic_data = mapping[str(topic_id)]
            keywords = ', '.join(topic_data['keywords'][:8])
            count = topic_counts[topic_id]
            
            with st.expander(f"📌 Topic {topic_id}: {keywords} ({count} papers)"):
                # Show sample papers
                topic_papers = theme_papers[theme_papers['topic_id'] == topic_id].head(5)
                
                for idx, paper in topic_papers.iterrows():
                    st.markdown(f"**{paper['title']}**")
                    st.caption(f"🏛️ {paper['university']} | 📅 {paper['date'].strftime('%Y-%m-%d')}")
                    if pd.notna(paper['abstract']) and paper['abstract']:
                        st.write(paper['abstract'][:300] + "...")
                    st.markdown("---")
    
    st.markdown("---")
    
    # Recent Papers
    st.subheader("📰 Recent Papers in This Theme")
    
    recent = theme_papers.nlargest(10, 'date')
    
    for idx, paper in recent.iterrows():
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"**{paper['title']}**")
                st.caption(f"🏛️ {paper['university']}")
            
            with col2:
                st.caption(f"📅 {paper['date'].strftime('%Y-%m-%d')}")
            
            if pd.notna(paper['abstract']) and paper['abstract']:
                with st.expander("View Abstract"):
                    st.write(paper['abstract'])
            
            st.markdown("---")

# ==================== EMERGING TOPICS PAGE ====================

elif page == "⚡ Emerging Topics":
    st.markdown('<p class="main-header">⚡ Emerging Research Topics</p>', unsafe_allow_html=True)
    
    st.markdown("""
    Topics showing **>50% growth** in recent quarters, indicating rapidly developing research areas
    that may present strategic opportunities for Babcock.
    """)
    
    st.markdown("---")
    
    emerging = trends['emerging_topics']
    
    # Growth threshold slider
    min_growth = st.slider(
        "Minimum Growth Rate",
        min_value=0,
        max_value=200,
        value=50,
        step=10,
        format="%d%%",
        help="Filter topics by minimum growth rate"
    )
    
    filtered_emerging = [t for t in emerging if t['growth_rate'] * 100 >= min_growth]
    
    st.info(f"**{len(filtered_emerging)} topics** with >{min_growth}% growth")
    
    st.markdown("---")
    
    # Display emerging topics
    for i, topic in enumerate(filtered_emerging, 1):
        keywords = ', '.join(topic['keywords'][:8])
        theme = topic['theme'].replace('_', ' ').title()
        growth = topic['growth_rate']
        recent = topic['recent_count']
        previous = topic['previous_count']
        
        # Color based on growth
        if growth > 1.5:
            color = "🔥"
        elif growth > 1.0:
            color = "⚡"
        else:
            color = "📈"
        
        with st.expander(f"{color} **#{i} - {keywords}** ({growth*100:+.0f}% growth)"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Theme", theme)
            
            with col2:
                st.metric("Growth Rate", f"{growth*100:+.0f}%")
            
            with col3:
                st.metric("Recent Quarter", f"{recent} papers", delta=f"+{recent-previous}")
            
            with col4:
                st.metric("Previous Quarter", f"{previous} papers")
            
            # Show sample papers
            st.markdown("**Sample Papers:**")
            
            topic_papers = papers_df[papers_df['topic_id'] == topic['topic_id']].nlargest(3, 'date')
            
            for idx, paper in topic_papers.iterrows():
                st.markdown(f"- **{paper['title']}**")
                st.caption(f"  {paper['university']} | {paper['date'].strftime('%Y-%m-%d')}")

# ==================== UNIVERSITIES PAGE ====================

elif page == "🏛️ Universities":
    st.markdown('<p class="main-header">🏛️ University Analysis</p>', unsafe_allow_html=True)
    
    # University rankings
    uni_counts = papers_df['university'].value_counts()
    
    st.markdown("---")
    
    # Overall ranking
    st.subheader("📊 Overall Research Output Rankings")
    
    fig = px.bar(
        x=uni_counts.head(15).values,
        y=uni_counts.head(15).index,
        orientation='h',
        title='Top 15 Universities by Total Papers',
        labels={'x': 'Number of Papers', 'y': 'University'},
        color=uni_counts.head(15).values,
        color_continuous_scale='Viridis'
    )
    fig.update_layout(height=600)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # University selector
    st.subheader("🔍 University Deep Dive")
    
    selected_uni = st.selectbox("Select University", sorted(papers_df['university'].unique()))
    
    uni_papers = papers_df[papers_df['university'] == selected_uni]
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Papers", f"{len(uni_papers):,}")
    
    with col2:
        st.metric("Themes", uni_papers['theme'].nunique())
    
    with col3:
        st.metric("Topics", uni_papers['topic_id'].nunique())
    
    with col4:
        quarterly_growth = uni_papers.groupby('quarter').size()
        if len(quarterly_growth) >= 2:
            growth = (quarterly_growth.iloc[-1] - quarterly_growth.iloc[-2]) / quarterly_growth.iloc[-2] * 100
            st.metric("Recent Growth", f"{growth:+.0f}%")
        else:
            st.metric("Recent Growth", "N/A")
    
    st.markdown("---")
    
    # Theme distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Research Themes")
        
        theme_dist = uni_papers['theme'].value_counts()
        
        fig = px.pie(
            values=theme_dist.values,
            names=[t.replace('_', ' ').title() for t in theme_dist.index],
            title=f'{selected_uni} - Theme Distribution'
        )
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Output Over Time")
        
        quarterly_uni = uni_papers.groupby('quarter').size().reset_index(name='count')
        quarterly_uni['quarter'] = quarterly_uni['quarter'].astype(str)
        
        fig = px.line(
            quarterly_uni,
            x='quarter',
            y='count',
            title=f'{selected_uni} - Quarterly Output',
            labels={'count': 'Papers', 'quarter': 'Quarter'},
            markers=True
        )
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Recent papers
    st.subheader(f"📰 Recent Papers from {selected_uni}")
    
    recent = uni_papers.nlargest(10, 'date')
    
    for idx, paper in recent.iterrows():
        theme = paper['theme'].replace('_', ' ').title()
        
        with st.container():
            st.markdown(f"**{paper['title']}**")
            st.caption(f"🎯 {theme} | 📅 {paper['date'].strftime('%Y-%m-%d')}")
            
            if pd.notna(paper['abstract']) and paper['abstract']:
                with st.expander("View Abstract"):
                    st.write(paper['abstract'])
            
            st.markdown("---")

# ==================== TRENDS OVER TIME PAGE ====================

elif page == "📈 Trends Over Time":
    st.markdown('<p class="main-header">📈 Temporal Trends Analysis</p>', unsafe_allow_html=True)
    
    st.markdown("""
    Quarterly breakdown showing how research themes evolve over the 24-month analysis period.
    """)
    
    st.markdown("---")
    
    # Overall trend
    st.subheader("📊 Overall Research Activity")
    
    quarterly_all = papers_df.groupby('quarter').size().reset_index(name='count')
    quarterly_all['quarter'] = quarterly_all['quarter'].astype(str)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=quarterly_all['quarter'],
        y=quarterly_all['count'],
        mode='lines+markers',
        name='Total Papers',
        line=dict(width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title='Quarterly Research Output (All Themes)',
        xaxis_title='Quarter',
        yaxis_title='Number of Papers',
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Theme-specific trends
    st.subheader("🎯 Trends by Theme")
    
    # Theme selector (multi-select)
    all_themes = sorted([t.replace('_', ' ').title() for t in papers_df['theme'].unique() if t != 'Other'])
    selected_themes = st.multiselect(
        "Select Themes to Compare",
        all_themes,
        default=all_themes[:3]
    )
    
    if selected_themes:
        # Filter data
        selected_themes_raw = [t.replace(' ', '_') for t in selected_themes]
        filtered_df = papers_df[papers_df['theme'].isin(selected_themes_raw)]
        
        quarterly_themes = filtered_df.groupby(['quarter', 'theme']).size().reset_index(name='count')
        quarterly_themes['quarter'] = quarterly_themes['quarter'].astype(str)
        quarterly_themes['theme'] = quarterly_themes['theme'].str.replace('_', ' ').str.title()
        
        fig = px.line(
            quarterly_themes,
            x='quarter',
            y='count',
            color='theme',
            title='Quarterly Trends - Selected Themes',
            labels={'count': 'Number of Papers', 'quarter': 'Quarter', 'theme': 'Theme'},
            markers=True
        )
        fig.update_layout(height=500, hovermode='x unified')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Growth rates table
        st.subheader("📊 Growth Rates by Theme")
        
        growth_data = []
        for theme in selected_themes_raw:
            theme_trend = trends['theme_trends'].get(theme, {})
            growth_data.append({
                'Theme': theme.replace('_', ' ').title(),
                'Total Papers': theme_trend.get('total_papers', 0),
                'Avg Growth Rate': f"{theme_trend.get('growth_rate', 0)*100:+.1f}%"
            })
        
        growth_df = pd.DataFrame(growth_data)
        st.dataframe(growth_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Heatmap
    st.subheader("🗺️ Theme Activity Heatmap")
    
    pivot = papers_df.groupby(['quarter', 'theme']).size().reset_index(name='count')
    pivot['quarter'] = pivot['quarter'].astype(str)
    pivot['theme'] = pivot['theme'].str.replace('_', ' ').str.title()
    pivot = pivot[pivot['theme'] != 'Other']
    pivot = pivot.pivot(index='theme', columns='quarter', values='count').fillna(0)
    
    fig = px.imshow(
        pivot,
        title='Research Activity Heatmap (Papers per Quarter)',
        labels=dict(x="Quarter", y="Theme", color="Papers"),
        aspect="auto",
        color_continuous_scale='YlOrRd'
    )
    fig.update_layout(height=600)
    
    st.plotly_chart(fig, use_container_width=True)

# ==================== FOOTER ====================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>Babcock Research Trends Analysis System</strong></p>
    <p>Powered by BERTopic | Data from OpenAlex | 24 Australasian Universities</p>
    <p>Last Updated: {}</p>
</div>
""".format(datetime.now().strftime("%B %d, %Y")), unsafe_allow_html=True)