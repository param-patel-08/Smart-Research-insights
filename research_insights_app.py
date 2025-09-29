"""
Smarter Research Insights - Advanced Data Analytics (Simplified Version)
Babcock Technology Investment Proposal Implementation
Uses CORE API for fetching papers and BERTopic for trend analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import json
import time
from typing import List, Dict, Tuple, Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# BERTopic and related imports
try:
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTOPIC_AVAILABLE = False
    st.warning("BERTopic not available. Running in limited mode.")

import warnings
warnings.filterwarnings('ignore')

# Initialize session state
if 'papers_df' not in st.session_state:
    st.session_state.papers_df = None
if 'topic_model' not in st.session_state:
    st.session_state.topic_model = None
if 'topics_info' not in st.session_state:
    st.session_state.topics_info = None

# Configuration
CORE_API_KEY = "icHUxkngRzK0PqTZl1paCoyw2Y3XV8tA"
CORE_API_BASE_URL = "https://api.core.ac.uk/v3"

# Babcock Technology Themes
BABCOCK_THEMES = [
    'Advanced Manufacturing',
    'Advanced Materials', 
    'Advanced Sensors',
    'AI and Automation',
    'Connectivity and Communications',
    'Data Integration, Computing and Analysis',
    'Energy and Sustainability',
    'Human Performance Augmentation',
    'Information and Communication Security'
]

# Australasian Universities (comprehensive list)
AUSTRALASIAN_UNIVERSITIES = [
    # Australian Universities
    'Australian National University', 'University of Canberra',
    'Macquarie University', 'University of New South Wales', 'University of Newcastle',
    'University of Sydney', 'University of Technology Sydney', 'Western Sydney University',
    'University of Wollongong', 'Charles Sturt University',
    'Central Queensland University', 'Griffith University', 'James Cook University',
    'Queensland University of Technology', 'University of Queensland',
    'University of Southern Queensland', 'University of the Sunshine Coast',
    'Bond University', 'University of South Australia', 'University of Adelaide',
    'Flinders University', 'Torrens University',
    'University of Tasmania', 'Deakin University', 'La Trobe University',
    'Monash University', 'RMIT University', 'Swinburne University of Technology',
    'University of Melbourne', 'Victoria University', 'Federation University',
    'Curtin University', 'Edith Cowan University', 'Murdoch University',
    'University of Western Australia', 'University of Notre Dame Australia',
    # New Zealand Universities
    'Auckland University of Technology', 'University of Auckland',
    'University of Waikato', 'Massey University', 'Victoria University of Wellington',
    'University of Canterbury', 'Lincoln University', 'University of Otago'
]

class COREAPIClient:
    """Client for interacting with CORE API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def search_papers(self, query: str, limit: int = 100, offset: int = 0) -> Dict:
        """Search papers using CORE API"""
        url = f"{CORE_API_BASE_URL}/search/works"
        
        params = {
            "q": query,
            "limit": limit,
            "offset": offset,
            "stats": True,
            "fulltext": False
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            st.error("API request timed out. Please try again.")
            return {"results": [], "totalHits": 0}
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return {"results": [], "totalHits": 0}
    
    def fetch_papers_for_universities(self, universities: List[str], 
                                     start_year: int = 2023, 
                                     max_papers_per_uni: int = 30) -> pd.DataFrame:
        """Fetch papers for multiple universities"""
        all_papers = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, university in enumerate(universities):
            status_text.text(f"Fetching papers from {university}...")
            
            # Create query for this university and time range
            query = f'(institutionName:"{university}" OR authors.affiliations:"{university}") AND (yearPublished>={start_year})'
            
            try:
                results = self.search_papers(query, limit=max_papers_per_uni)
                
                for paper in results.get('results', []):
                    # Extract relevant information
                    paper_data = {
                        'title': paper.get('title', 'No Title'),
                        'abstract': paper.get('abstract', ''),
                        'authors': ', '.join([author.get('name', '') for author in paper.get('authors', [])]),
                        'year': paper.get('yearPublished', start_year),
                        'university': university,
                        'doi': paper.get('doi', ''),
                        'downloadUrl': paper.get('downloadUrl', ''),
                        'publishedDate': paper.get('publishedDate', ''),
                        'language': paper.get('language', {}).get('name', 'English')
                    }
                    
                    # Only include papers with abstracts for topic modeling
                    if paper_data['abstract'] and len(paper_data['abstract']) > 100:
                        all_papers.append(paper_data)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                st.warning(f"Could not fetch papers from {university}: {e}")
            
            progress_bar.progress((idx + 1) / len(universities))
        
        status_text.text("Paper fetching complete!")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
        return pd.DataFrame(all_papers)

class SimpleBERTopicAnalyzer:
    """Simplified BERTopic implementation"""
    
    def __init__(self, n_topics: int = 15):
        self.n_topics = n_topics
        self.topic_model = None
        self.theme_embeddings = None
        
        if BERTOPIC_AVAILABLE:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            self._prepare_theme_embeddings()
    
    def _prepare_theme_embeddings(self):
        """Pre-compute embeddings for Babcock themes"""
        if not BERTOPIC_AVAILABLE:
            return
            
        theme_descriptions = [
            "Advanced Manufacturing: robotics, automation, 3D printing, smart factories, industrial IoT",
            "Advanced Materials: composites, nanomaterials, smart materials, material science, polymers",
            "Advanced Sensors: sensing technology, IoT sensors, environmental monitoring, detection systems",
            "AI and Automation: artificial intelligence, machine learning, deep learning, neural networks, automation",
            "Connectivity and Communications: 5G, wireless networks, telecommunications, network protocols",
            "Data Integration, Computing and Analysis: big data, cloud computing, data analytics, databases",
            "Energy and Sustainability: renewable energy, green technology, sustainability, environmental protection",
            "Human Performance Augmentation: human-machine interface, ergonomics, cognitive enhancement, wearables",
            "Information and Communication Security: cybersecurity, encryption, network security, data protection"
        ]
        self.theme_embeddings = self.sentence_model.encode(theme_descriptions)
    
    def fit_transform(self, documents: List[str], abstracts: List[str]) -> Tuple:
        """Fit BERTopic model and transform documents"""
        if not BERTOPIC_AVAILABLE:
            # Return dummy topics if BERTopic not available
            return list(range(len(abstracts))), [0.5] * len(abstracts)
        
        # Configure BERTopic
        vectorizer_model = CountVectorizer(
            stop_words="english",
            min_df=2,
            max_df=0.95,
            ngram_range=(1, 2)
        )
        
        self.topic_model = BERTopic(
            embedding_model=self.sentence_model,
            vectorizer_model=vectorizer_model,
            nr_topics=self.n_topics,
            top_n_words=10,
            calculate_probabilities=True,
            verbose=False
        )
        
        # Fit the model
        topics, probs = self.topic_model.fit_transform(abstracts)
        
        return topics, probs
    
    def map_to_babcock_themes(self, topic_words: List[str]) -> Dict[str, float]:
        """Map discovered topics to Babcock themes using similarity"""
        if not BERTOPIC_AVAILABLE or self.theme_embeddings is None:
            # Return equal distribution if not available
            return {theme: 1.0/len(BABCOCK_THEMES) for theme in BABCOCK_THEMES}
        
        topic_text = " ".join(topic_words)
        topic_embedding = self.sentence_model.encode([topic_text])
        
        similarities = cosine_similarity(topic_embedding, self.theme_embeddings)[0]
        
        theme_mapping = {}
        for idx, theme in enumerate(BABCOCK_THEMES):
            theme_mapping[theme] = float(similarities[idx])
        
        return theme_mapping
    
    def get_topic_info(self) -> pd.DataFrame:
        """Get detailed topic information with theme mapping"""
        if self.topic_model is None:
            return pd.DataFrame()
        
        topic_info = self.topic_model.get_topic_info()
        
        # Add Babcock theme mapping
        theme_mappings = []
        for idx, row in topic_info.iterrows():
            if row['Topic'] != -1:  # Skip outlier topic
                topic_words = [word for word, _ in self.topic_model.get_topic(row['Topic'])]
                mapping = self.map_to_babcock_themes(topic_words)
                best_theme = max(mapping, key=mapping.get)
                theme_mappings.append(best_theme)
            else:
                theme_mappings.append("Uncategorized")
        
        topic_info['Babcock_Theme'] = theme_mappings
        
        return topic_info

# Visualization functions
def create_topic_evolution_plot(papers_df: pd.DataFrame) -> go.Figure:
    """Create topic evolution over time visualization"""
    if 'year' not in papers_df.columns or 'topic' not in papers_df.columns:
        return go.Figure()
    
    evolution_data = papers_df.groupby(['year', 'topic']).size().reset_index(name='count')
    
    fig = px.area(
        evolution_data,
        x='year',
        y='count',
        color='topic',
        title='Topic Evolution Over Time',
        labels={'count': 'Number of Papers', 'year': 'Year', 'topic': 'Topic ID'}
    )
    
    fig.update_layout(height=500)
    return fig

def create_university_ranking(papers_df: pd.DataFrame, selected_theme: str = None) -> pd.DataFrame:
    """Create university ranking based on paper count and topics"""
    if selected_theme and selected_theme != 'All':
        filtered_df = papers_df[papers_df['babcock_theme'] == selected_theme]
    else:
        filtered_df = papers_df
    
    ranking = filtered_df.groupby('university').agg({
        'title': 'count',
        'topic': lambda x: x.nunique() if 'topic' in filtered_df.columns else 0
    }).reset_index()
    
    ranking.columns = ['University', 'Paper Count', 'Topic Diversity']
    ranking = ranking.sort_values('Paper Count', ascending=False)
    
    return ranking

def create_theme_distribution_plot(papers_df: pd.DataFrame) -> go.Figure:
    """Create pie chart of Babcock theme distribution"""
    if 'babcock_theme' not in papers_df.columns:
        return go.Figure()
        
    theme_counts = papers_df['babcock_theme'].value_counts()
    
    fig = px.pie(
        values=theme_counts.values,
        names=theme_counts.index,
        title='Distribution of Papers Across Babcock Technology Themes',
        hole=0.3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=500)
    
    return fig

def export_results(papers_df: pd.DataFrame, topic_info: pd.DataFrame) -> bytes:
    """Export results to Excel file"""
    import io
    
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            papers_df.to_excel(writer, sheet_name='Papers', index=False)
            if not topic_info.empty:
                topic_info.to_excel(writer, sheet_name='Topics', index=False)
            
            ranking = create_university_ranking(papers_df)
            ranking.to_excel(writer, sheet_name='University Ranking', index=False)
    except Exception as e:
        st.error(f"Export error: {e}")
        return b""
    
    return output.getvalue()

# Main Streamlit App
def main():
    st.set_page_config(
        page_title="Smarter Research Insights",
        page_icon="🔬",
        layout="wide"
    )
    
    st.title("🔬 Smarter Research Insights - Advanced Data Analytics")
    st.markdown("**Babcock Technology Investment Proposal** - Analyzing Australasian University Research Trends")
    
    # Check for missing dependencies
    if not BERTOPIC_AVAILABLE:
        st.warning("⚠️ Running in limited mode. Some features may be unavailable.")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Configuration")
        
        # University selection
        st.subheader("Universities")
        select_all = st.checkbox("Select All Universities", value=False)
        
        if select_all:
            selected_universities = AUSTRALASIAN_UNIVERSITIES
        else:
            selected_universities = st.multiselect(
                "Select Universities",
                options=AUSTRALASIAN_UNIVERSITIES,
                default=AUSTRALASIAN_UNIVERSITIES[:5]
            )
        
        # Time range
        st.subheader("Time Range")
        start_year = st.selectbox("Start Year", options=[2023, 2024], index=0)
        
        # Topic modeling parameters
        st.subheader("Topic Modeling")
        n_topics = st.slider("Number of Topics", min_value=10, max_value=20, value=15)
        
        # Fetch papers button
        if st.button("🔍 Fetch Papers & Analyze", type="primary"):
            if not selected_universities:
                st.error("Please select at least one university")
            else:
                with st.spinner("Fetching papers from CORE API..."):
                    # Initialize API client
                    api_client = COREAPIClient(CORE_API_KEY)
                    
                    # Fetch papers
                    papers_df = api_client.fetch_papers_for_universities(
                        selected_universities,
                        start_year=start_year,
                        max_papers_per_uni=20  # Reduced for faster demo
                    )
                    
                    if not papers_df.empty:
                        st.success(f"✅ Fetched {len(papers_df)} papers!")
                        
                        # Perform topic modeling if available
                        if BERTOPIC_AVAILABLE:
                            with st.spinner("Performing topic modeling with BERTopic..."):
                                analyzer = SimpleBERTopicAnalyzer(n_topics=n_topics)
                                
                                # Fit the model
                                topics, probs = analyzer.fit_transform(
                                    papers_df['title'].tolist(),
                                    papers_df['abstract'].tolist()
                                )
                                
                                papers_df['topic'] = topics
                                papers_df['topic_probability'] = probs if isinstance(probs, list) else probs.max(axis=1) if len(probs.shape) > 1 else [0.5] * len(papers_df)
                                
                                # Get topic info with theme mapping
                                topic_info = analyzer.get_topic_info()
                                
                                # Map papers to Babcock themes
                                if not topic_info.empty:
                                    topic_to_theme = dict(zip(topic_info['Topic'], topic_info['Babcock_Theme']))
                                    papers_df['babcock_theme'] = papers_df['topic'].map(topic_to_theme).fillna('Uncategorized')
                                else:
                                    papers_df['babcock_theme'] = 'Uncategorized'
                                
                                st.success("✅ Topic modeling complete!")
                        else:
                            # Assign random themes if BERTopic not available
                            papers_df['topic'] = range(len(papers_df))
                            papers_df['babcock_theme'] = np.random.choice(BABCOCK_THEMES, size=len(papers_df))
                            topic_info = pd.DataFrame()
                        
                        # Store in session state
                        st.session_state.papers_df = papers_df
                        st.session_state.topics_info = topic_info
                        
                    else:
                        st.error("No papers found. Please try different universities or check the API connection.")
    
    # Main content area
    if st.session_state.papers_df is not None:
        papers_df = st.session_state.papers_df
        topic_info = st.session_state.topics_info if st.session_state.topics_info is not None else pd.DataFrame()
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Papers", len(papers_df))
        with col2:
            st.metric("Universities", papers_df['university'].nunique())
        with col3:
            n_topics_found = len(topic_info[topic_info['Topic'] != -1]) if not topic_info.empty else 0
            st.metric("Topics Discovered", n_topics_found)
        with col4:
            st.metric("Themes Covered", papers_df['babcock_theme'].nunique() if 'babcock_theme' in papers_df.columns else 0)
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview", 
            "🏛️ University Rankings", 
            "🎯 Theme Analysis",
            "🔍 Search Papers"
        ])
        
        with tab1:
            st.header("Research Overview")
            
            # Topic evolution plot
            if 'topic' in papers_df.columns:
                fig = create_topic_evolution_plot(papers_df)
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent papers
            st.subheader("Recent Papers")
            recent_papers = papers_df.nlargest(5, 'year')[['title', 'university', 'year', 'babcock_theme']]
            st.dataframe(recent_papers, use_container_width=True)
        
        with tab2:
            st.header("University Rankings")
            
            # Filter by theme
            theme_filter = st.selectbox(
                "Filter by Theme",
                options=['All'] + list(BABCOCK_THEMES),
                key='ranking_theme'
            )
            
            ranking_df = create_university_ranking(papers_df, theme_filter)
            
            # Display ranking
            st.dataframe(ranking_df, use_container_width=True)
            
            # Visualization
            if not ranking_df.empty:
                fig = px.bar(
                    ranking_df.head(10),
                    x='Paper Count',
                    y='University',
                    orientation='h',
                    title='Top 10 Universities by Paper Count',
                    color='Topic Diversity',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.header("Babcock Theme Analysis")
            
            # Theme distribution
            fig = create_theme_distribution_plot(papers_df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Theme details
            if 'babcock_theme' in papers_df.columns:
                st.subheader("Papers by Theme")
                theme_counts = papers_df.groupby('babcock_theme').agg({
                    'title': 'count',
                    'university': lambda x: x.nunique()
                }).reset_index()
                theme_counts.columns = ['Theme', 'Paper Count', 'Universities Involved']
                theme_counts = theme_counts.sort_values('Paper Count', ascending=False)
                st.dataframe(theme_counts, use_container_width=True)
        
        with tab4:
            st.header("Search & Filter Papers")
            
            # Search functionality
            col1, col2 = st.columns(2)
            with col1:
                search_query = st.text_input("Search by keyword", placeholder="Enter keyword...")
            with col2:
                theme_filter = st.selectbox(
                    "Filter by Theme",
                    options=['All'] + list(BABCOCK_THEMES),
                    key='search_theme'
                )
            
            # Apply filters
            filtered_df = papers_df.copy()
            
            if search_query:
                mask = (
                    filtered_df['title'].str.contains(search_query, case=False, na=False) |
                    filtered_df['abstract'].str.contains(search_query, case=False, na=False)
                )
                filtered_df = filtered_df[mask]
            
            if theme_filter != 'All' and 'babcock_theme' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['babcock_theme'] == theme_filter]
            
            st.subheader(f"Found {len(filtered_df)} papers")
            
            # Display papers
            for idx, row in filtered_df.head(10).iterrows():
                with st.expander(f"📄 {row['title'][:100]}..."):
                    st.markdown(f"**University:** {row['university']}")
                    st.markdown(f"**Year:** {row['year']}")
                    if 'babcock_theme' in row:
                        st.markdown(f"**Theme:** {row['babcock_theme']}")
                    st.markdown(f"**Abstract:** {row['abstract'][:500]}...")
                    if row['doi']:
                        st.markdown(f"**DOI:** {row['doi']}")
        
        # Export functionality
        st.sidebar.divider()
        st.sidebar.subheader("Export Results")
        if st.sidebar.button("📥 Export to Excel"):
            excel_data = export_results(papers_df, topic_info)
            if excel_data:
                st.sidebar.download_button(
                    label="Download Excel Report",
                    data=excel_data,
                    file_name=f"research_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    else:
        # Welcome screen
        st.info("👈 Please configure settings in the sidebar and click 'Fetch Papers & Analyze' to begin")
        
        st.markdown("### About This Tool")
        st.markdown("""
        This tool provides advanced analytics for research trends from Australasian universities:
        
        - **Real-time Data**: Fetches actual research papers from CORE API
        - **Topic Modeling**: Discovers research topics (when BERTopic is available)
        - **Theme Mapping**: Maps research to Babcock's 9 technology themes
        - **Interactive Visualizations**: Explore trends and rankings
        - **Export Capabilities**: Download results for further analysis
        
        ### Babcock Technology Themes
        """)
        
        # Display themes in columns
        theme_cols = st.columns(3)
        for idx, theme in enumerate(BABCOCK_THEMES):
            with theme_cols[idx % 3]:
                st.markdown(f"• {theme}")

if __name__ == "__main__":
    main()