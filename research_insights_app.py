"""
Smarter Research Insights - Advanced Data Analytics
Babcock Technology Investment Proposal Implementation
Complete Updated Version with All Fixes
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
import os
from dotenv import load_dotenv
import nltk

# Download NLTK data at startup
@st.cache_resource
def download_nltk_data():
    try:
        nltk.data.find('corpora/stopwords')
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)

download_nltk_data()
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

# Load environment variables
load_dotenv()

# Initialize session state
if 'papers_df' not in st.session_state:
    st.session_state.papers_df = None
if 'topic_model' not in st.session_state:
    st.session_state.topic_model = None
if 'topics_info' not in st.session_state:
    st.session_state.topics_info = None

# Configuration - Load API key securely
def get_api_key():
    """Get API key from environment or use the valid one"""
    # Try environment variable first
    api_key = os.getenv("CORE_API_KEY")
    if api_key:
        return api_key
    
    # Try Streamlit secrets
    try:
        return st.secrets["CORE_API_KEY"]
    except:
        pass
    
    # Use your valid hardcoded key as fallback (expires Sept 30, 2025)
    return "icHUxkngRzK0PqTZl1paCoyw2Y3XV8tA"

# Get the API key
CORE_API_KEY = get_api_key()
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

# Theme keywords for better matching
THEME_KEYWORDS = {
    'Advanced Manufacturing': ['manufacturing', 'robotics', 'automation', '3d printing', 'factory', 'production', 'industrial', 'additive', 'smart factory'],
    'Advanced Materials': ['materials', 'composites', 'nanomaterials', 'polymers', 'alloys', 'ceramics', 'coatings', 'graphene', 'metamaterials'],
    'Advanced Sensors': ['sensor', 'sensing', 'detection', 'monitoring', 'measurement', 'instrumentation', 'transducer', 'biosensor', 'IoT sensor'],
    'AI and Automation': ['artificial intelligence', 'machine learning', 'deep learning', 'neural network', 'algorithm', 'automation', 'AI', 'NLP', 'computer vision'],
    'Connectivity and Communications': ['5g', 'wireless', 'network', 'communication', 'telecommunications', 'broadband', 'internet', 'satellite', 'RF'],
    'Data Integration, Computing and Analysis': ['data', 'analytics', 'computing', 'cloud', 'database', 'integration', 'big data', 'data science', 'visualization'],
    'Energy and Sustainability': ['energy', 'renewable', 'sustainable', 'solar', 'wind', 'battery', 'green', 'environmental', 'carbon'],
    'Human Performance Augmentation': ['human', 'augmentation', 'wearable', 'ergonomics', 'interface', 'enhancement', 'cognitive', 'exoskeleton', 'HCI'],
    'Information and Communication Security': ['security', 'cybersecurity', 'encryption', 'privacy', 'authentication', 'blockchain', 'cryptography', 'firewall', 'malware']
}

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
    """FIXED Client that actually gets papers from CORE API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.core.ac.uk/v3"
    
    def search_papers(self, query: str, limit: int = 100, offset: int = 0) -> Dict:
        """Search papers using CORE API v3"""
        url = f"{self.base_url}/search/works"
        
        params = {
            "q": query,
            "limit": limit,
            "offset": offset,
            "apiKey": self.api_key
        }
        
        headers = {"Accept": "application/json"}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=60)
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error {response.status_code}")
                return {"results": [], "totalHits": 0}
                
        except requests.exceptions.Timeout:
            st.warning("Request timed out - trying simpler query")
            return {"results": [], "totalHits": 0}
        except Exception as e:
            st.error(f"API Error: {e}")
            return {"results": [], "totalHits": 0}
    
    def fetch_papers_for_universities(self, universities: List[str], 
                                     start_year: int = 2023, 
                                     max_papers_per_uni: int = 30,
                                     theme_filter: str = None) -> pd.DataFrame:
        """WORKING METHOD: Use simple text search, not institutionName"""
        all_papers = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        universities_to_process = universities[:10]
        
        if len(universities) > 10:
            st.warning("⚠️ Processing first 10 universities to avoid rate limits")
        
        for idx, university in enumerate(universities_to_process):
            status_text.text(f"Searching for papers from {university}...")
            
            # Use simple text search with university name in quotes
            query = f'"{university}"'
            
            # Add year filter carefully
            if start_year == 2024:
                query = f'{query} 2024'
            elif start_year == 2023:
                query = f'{query} (2023 OR 2024)'
            
            try:
                results = self.search_papers(query, limit=max_papers_per_uni)
                
                total_found = results.get('totalHits', 0)
                papers_processed = 0
                
                status_text.text(f"Found {total_found:,} papers mentioning {university}")
                
                for paper in results.get('results', []):
                    # Check if paper is actually from this university
                    is_from_uni = False
                    actual_affiliation = "Unknown"
                    
                    if paper.get('authors'):
                        for author in paper.get('authors', []):
                            if author.get('affiliations'):
                                aff_text = str(author.get('affiliations', '')).lower()
                                uni_lower = university.lower()
                                
                                if uni_lower in aff_text or any(word in aff_text for word in uni_lower.split()[:2]):
                                    is_from_uni = True
                                    actual_affiliation = author.get('affiliations', '')[:200]
                                    break
                    
                    # Create paper data
                    paper_data = {
                        'title': paper.get('title', 'No Title'),
                        'abstract': paper.get('abstract', ''),
                        'authors': ', '.join([
                            author.get('name', '') 
                            for author in paper.get('authors', [])
                        ]) if paper.get('authors') else 'Unknown',
                        'year': paper.get('yearPublished', 2023),
                        'university': university,
                        'actual_affiliation': actual_affiliation,
                        'doi': paper.get('doi', ''),
                        'downloadUrl': paper.get('downloadUrl', ''),
                        'publishedDate': paper.get('publishedDate', ''),
                        'is_verified': is_from_uni
                    }
                    
                    # Only add if has abstract
                    if paper_data['abstract'] and len(paper_data['abstract']) > 50:
                        all_papers.append(paper_data)
                        papers_processed += 1
                
                status_text.text(f"Added {papers_processed} papers from {university}")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                st.warning(f"Error fetching from {university}: {e}")
            
            progress_bar.progress((idx + 1) / len(universities_to_process))
        
        status_text.text(f"✅ Complete! Found {len(all_papers)} papers with abstracts")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
        if len(all_papers) == 0:
            st.error("No papers found! Try selecting fewer universities")
        else:
            df = pd.DataFrame(all_papers)
            verified_count = len(df[df['is_verified'] == True]) if 'is_verified' in df.columns else 0
            st.info(f"📊 Found {len(df)} papers total ({verified_count} verified from selected universities)")
        
        return pd.DataFrame(all_papers)
    
    def matches_theme(self, text: str, theme: str) -> bool:
        """Check if text matches theme keywords"""
        text_lower = text.lower()
        keywords = THEME_KEYWORDS.get(theme, [])
        return any(keyword in text_lower for keyword in keywords)

class OnlineBERTopicAnalyzer:
    """Online BERTopic implementation for dynamic topic modeling"""
    
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
            
        theme_descriptions = []
        for theme, keywords in THEME_KEYWORDS.items():
            desc = f"{theme}: {', '.join(keywords)}"
            theme_descriptions.append(desc)
        
        self.theme_embeddings = self.sentence_model.encode(theme_descriptions)
    
    def fit_transform(self, documents: List[str], abstracts: List[str]) -> Tuple:
        """Fit BERTopic model and transform documents"""
        if not BERTOPIC_AVAILABLE:
            return list(range(len(abstracts))), [0.5] * len(abstracts)
        
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
        
        topics, probs = self.topic_model.fit_transform(abstracts)
        
        return topics, probs
    
    def map_to_babcock_themes(self, topic_words: List[str]) -> Dict[str, float]:
        """Map discovered topics to Babcock themes using similarity"""
        if not BERTOPIC_AVAILABLE or self.theme_embeddings is None:
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
        
        theme_mappings = []
        for idx, row in topic_info.iterrows():
            if row['Topic'] != -1:
                topic_words = [word for word, _ in self.topic_model.get_topic(row['Topic'])]
                mapping = self.map_to_babcock_themes(topic_words)
                best_theme = max(mapping, key=mapping.get)
                theme_mappings.append(best_theme)
            else:
                theme_mappings.append("Uncategorized")
        
        topic_info['Babcock_Theme'] = theme_mappings
        
        return topic_info

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
    
    if filtered_df.empty:
        return pd.DataFrame(columns=['University', 'Paper Count', 'Topic Diversity'])
    
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
        st.info("ℹ️ Running in limited mode. Install BERTopic for full functionality.")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Debug mode
        debug_mode = st.checkbox("🐛 Debug Mode", value=False)
        if debug_mode:
            st.success(f"✅ API Key loaded: {CORE_API_KEY[:10]}...")
            st.info(f"Base URL: {CORE_API_BASE_URL}")
        
        st.divider()
        
        # Theme Filter (NEW!)
        st.subheader("🎯 Research Theme Filter")
        theme_filter = st.selectbox(
            "Select Technology Theme",
            options=['All'] + BABCOCK_THEMES,
            help="Filter papers by Babcock technology themes"
        )
        
        if theme_filter != 'All':
            st.info(f"📌 Filtering for: {theme_filter}")
            keywords = THEME_KEYWORDS.get(theme_filter, [])
            with st.expander("View theme keywords"):
                st.write(", ".join(keywords))
        
        st.divider()
        
        # University selection
        st.subheader("🏛️ Universities")
        
        # Quick select options
        quick_select = st.radio(
            "Quick Selection",
            ["Custom", "Top 5", "All Australian", "All NZ", "All Universities"],
            horizontal=True
        )
        
        if quick_select == "Custom":
            selected_universities = st.multiselect(
                "Select Universities",
                options=AUSTRALASIAN_UNIVERSITIES,
                default=AUSTRALASIAN_UNIVERSITIES[:5]
            )
        elif quick_select == "Top 5":
            selected_universities = [
                'University of Melbourne',
                'University of Sydney',
                'Australian National University',
                'University of Queensland',
                'Monash University'
            ]
        elif quick_select == "All Australian":
            selected_universities = [uni for uni in AUSTRALASIAN_UNIVERSITIES if uni not in [
                'Auckland University of Technology', 'University of Auckland',
                'University of Waikato', 'Massey University', 
                'Victoria University of Wellington', 'University of Canterbury',
                'Lincoln University', 'University of Otago'
            ]]
        elif quick_select == "All NZ":
            selected_universities = [
                'Auckland University of Technology', 'University of Auckland',
                'University of Waikato', 'Massey University',
                'Victoria University of Wellington', 'University of Canterbury',
                'Lincoln University', 'University of Otago'
            ]
        else:
            selected_universities = AUSTRALASIAN_UNIVERSITIES
        
        st.info(f"📊 {len(selected_universities)} universities selected")
        
        st.divider()
        
        # Time range
        st.subheader("📅 Time Range")
        start_year = st.selectbox("Start Year", options=[2023, 2024], index=0)
        
        # Papers per university
        max_papers = st.slider(
            "Max Papers per University",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="Reduce this to speed up fetching"
        )
        
        st.divider()
        
        # Topic modeling parameters
        st.subheader("🧠 Topic Modeling")
        n_topics = st.slider("Number of Topics", min_value=10, max_value=20, value=15)
        
        st.divider()
        
        # Fetch papers button
        if st.button("🔍 Fetch Papers & Analyze", type="primary", use_container_width=True):
            if not selected_universities:
                st.error("Please select at least one university")
            else:
                with st.spinner("Fetching papers from CORE API..."):
                    # Initialize API client
                    api_client = COREAPIClient(CORE_API_KEY)
                    
                    # Fetch papers with theme filter
                    papers_df = api_client.fetch_papers_for_universities(
                        selected_universities,
                        start_year=start_year,
                        max_papers_per_uni=max_papers,
                        theme_filter=theme_filter  # Pass theme filter
                    )
                    
                    if not papers_df.empty:
                        st.success(f"✅ Fetched {len(papers_df)} papers!")
                        
                        # Perform topic modeling if available
                        if BERTOPIC_AVAILABLE and len(papers_df) > 5:
                            with st.spinner("Performing topic modeling with BERTopic..."):
                                analyzer = OnlineBERTopicAnalyzer(n_topics=n_topics)
                                
                                topics, probs = analyzer.fit_transform(
                                    papers_df['title'].tolist(),
                                    papers_df['abstract'].tolist()
                                )
                                
                                papers_df['topic'] = topics
                                papers_df['topic_probability'] = probs if isinstance(probs, list) else probs.max(axis=1) if len(probs.shape) > 1 else [0.5] * len(papers_df)
                                
                                topic_info = analyzer.get_topic_info()
                                
                                if not topic_info.empty:
                                    topic_to_theme = dict(zip(topic_info['Topic'], topic_info['Babcock_Theme']))
                                    papers_df['babcock_theme'] = papers_df['topic'].map(topic_to_theme).fillna('Uncategorized')
                                else:
                                    papers_df['babcock_theme'] = 'Uncategorized'
                                
                                st.success("✅ Topic modeling complete!")
                        else:
                            # Assign themes based on keywords if BERTopic not available
                            papers_df['topic'] = range(len(papers_df))
                            papers_df['babcock_theme'] = papers_df.apply(
                                lambda row: assign_theme_by_keywords(
                                    row['title'] + ' ' + row['abstract']
                                ), axis=1
                            )
                            topic_info = pd.DataFrame()
                        
                        # Store in session state
                        st.session_state.papers_df = papers_df
                        st.session_state.topics_info = topic_info
                        
                    else:
                        st.error("No papers found. Try different settings or check the API connection.")
    
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
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Topic Analysis", 
            "🏛️ University Rankings", 
            "🎯 Theme Mapping",
            "🔍 Search & Filter",
            "📈 Emerging Trends"
        ])
        
        with tab1:
            st.header("Topic Analysis")
            
            # Topic evolution plot
            if 'topic' in papers_df.columns:
                fig = create_topic_evolution_plot(papers_df)
                st.plotly_chart(fig, use_container_width=True)
            
            # Topic details
            if not topic_info.empty:
                st.subheader("Discovered Topics")
                display_topics = topic_info[topic_info['Topic'] != -1][['Topic', 'Count', 'Name', 'Babcock_Theme']]
                st.dataframe(display_topics, use_container_width=True)
            
            # Top papers by topic
            st.subheader("Sample Papers by Topic")
            if 'topic' in papers_df.columns:
                selected_topic = st.selectbox("Select Topic", papers_df['topic'].unique())
                topic_papers = papers_df[papers_df['topic'] == selected_topic].head(3)
                for idx, row in topic_papers.iterrows():
                    with st.expander(f"📄 {row['title'][:100]}..."):
                        st.write(f"**University:** {row['university']}")
                        st.write(f"**Year:** {row['year']}")
                        st.write(f"**Abstract:** {row['abstract'][:300]}...")
        
        with tab2:
            st.header("University Rankings")
            
            # Filter by theme
            ranking_theme_filter = st.selectbox(
                "Filter by Theme",
                options=['All'] + list(BABCOCK_THEMES),
                key='ranking_theme'
            )
            
            ranking_df = create_university_ranking(papers_df, ranking_theme_filter)
            
            if not ranking_df.empty:
                # Display ranking
                st.dataframe(ranking_df, use_container_width=True)
                
                # Visualization
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
            else:
                st.info("No data available for the selected theme")
        
        with tab3:
            st.header("Babcock Theme Mapping")
            
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
                
                # Theme-specific papers
                st.subheader("Explore Papers by Theme")
                selected_theme = st.selectbox("Select Theme", BABCOCK_THEMES)
                theme_papers = papers_df[papers_df['babcock_theme'] == selected_theme].head(5)
                
                for idx, row in theme_papers.iterrows():
                    with st.expander(f"📄 {row['title'][:100]}..."):
                        st.write(f"**University:** {row['university']}")
                        st.write(f"**Year:** {row['year']}")
                        if row['doi']:
                            st.write(f"**DOI:** {row['doi']}")
                        st.write(f"**Abstract:** {row['abstract'][:500]}...")
        
        with tab4:
            st.header("Search & Filter Papers")
            
            # Search functionality
            col1, col2, col3 = st.columns(3)
            with col1:
                search_query = st.text_input("Search by keyword", placeholder="Enter keyword...")
            with col2:
                search_theme_filter = st.selectbox(
                    "Filter by Theme",
                    options=['All'] + list(BABCOCK_THEMES),
                    key='search_theme'
                )
            with col3:
                search_uni_filter = st.selectbox(
                    "Filter by University",
                    options=['All'] + list(papers_df['university'].unique()),
                    key='search_uni'
                )
            
            # Apply filters
            filtered_df = papers_df.copy()
            
            if search_query:
                mask = (
                    filtered_df['title'].str.contains(search_query, case=False, na=False) |
                    filtered_df['abstract'].str.contains(search_query, case=False, na=False)
                )
                filtered_df = filtered_df[mask]
            
            if search_theme_filter != 'All' and 'babcock_theme' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['babcock_theme'] == search_theme_filter]
            
            if search_uni_filter != 'All':
                filtered_df = filtered_df[filtered_df['university'] == search_uni_filter]
            
            st.subheader(f"Found {len(filtered_df)} papers")
            
            # Display papers
            for idx, row in filtered_df.head(20).iterrows():
                with st.expander(f"📄 {row['title'][:100]}..."):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**University:** {row['university']}")
                        st.markdown(f"**Year:** {row['year']}")
                        if 'babcock_theme' in row:
                            st.markdown(f"**Theme:** {row['babcock_theme']}")
                        st.markdown(f"**Abstract:** {row['abstract'][:500]}...")
                    with col2:
                        if row['doi']:
                            st.markdown(f"**DOI:** {row['doi']}")
                        if row['downloadUrl']:
                            st.markdown(f"[📥 Download]({row['downloadUrl']})")
        
        with tab5:
            st.header("Emerging Research Trends")
            
            # Calculate trend growth
            st.subheader("Rapidly Growing Topics")
            
            if 'year' in papers_df.columns and 'babcock_theme' in papers_df.columns:
                # Get recent year data
                recent_papers = papers_df[papers_df['year'] >= papers_df['year'].max()]
                topic_growth = recent_papers['babcock_theme'].value_counts().head(5)
                
                fig = px.bar(
                    x=topic_growth.values,
                    y=topic_growth.index,
                    orientation='h',
                    title='Top Growing Themes (Recent Period)',
                    labels={'x': 'Paper Count', 'y': 'Theme'},
                    color=topic_growth.values,
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Keyword trends
            st.subheader("Trending Keywords")
            if 'abstract' in papers_df.columns:
                # Extract common words from recent papers
                recent_abstracts = ' '.join(papers_df.head(50)['abstract'].dropna())
                words = recent_abstracts.lower().split()
                
                # Remove common words
                stop_words = {'the', 'and', 'of', 'to', 'in', 'a', 'is', 'for', 'on', 'with', 'as', 'by', 'that', 'this', 'from', 'are', 'an', 'be', 'has', 'have', 'was', 'were', 'been', 'being'}
                filtered_words = [w for w in words if len(w) > 4 and w not in stop_words]
                
                # Count frequencies
                from collections import Counter
                word_freq = Counter(filtered_words).most_common(20)
                
                # Display as bar chart
                if word_freq:
                    words_df = pd.DataFrame(word_freq, columns=['Word', 'Frequency'])
                    fig = px.bar(words_df, x='Frequency', y='Word', orientation='h',
                                title='Most Frequent Keywords in Recent Papers')
                    fig.update_layout(height=600)
                    st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 Advanced trend analysis features can be enhanced with more historical data")
        
        # Export functionality
        st.sidebar.divider()
        st.sidebar.subheader("📥 Export Results")
        if st.sidebar.button("Generate Excel Report", use_container_width=True):
            excel_data = export_results(papers_df, topic_info)
            if excel_data:
                st.sidebar.download_button(
                    label="📥 Download Excel Report",
                    data=excel_data,
                    file_name=f"research_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    else:
        # Welcome screen
        st.info("👈 Please configure settings in the sidebar and click 'Fetch Papers & Analyze' to begin")
        
        # Display instructions in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🚀 Getting Started")
            st.markdown("""
            1. **Select Theme** (optional) - Focus on specific technology area
            2. **Choose Universities** - Quick select or custom selection
            3. **Set Time Range** - Papers from 2023 or 2024
            4. **Adjust Parameters** - Papers per university and topic count
            5. **Click 'Fetch Papers & Analyze'** - Start the analysis
            """)
            
            st.markdown("### 📊 Features")
            st.markdown("""
            - Real-time paper fetching from CORE API
            - Dynamic topic modeling with BERTopic
            - Automatic theme categorization
            - University rankings and comparisons
            - Trend analysis and emerging topics
            - Export results to Excel
            """)
        
        with col2:
            st.markdown("### 🎯 Babcock Technology Themes")
            for i, theme in enumerate(BABCOCK_THEMES, 1):
                st.markdown(f"{i}. {theme}")
            
            st.markdown("### ℹ️ About")
            st.markdown("""
            This tool analyzes research trends from Australasian universities,
            mapping them to Babcock's strategic technology themes for insights
            into emerging research areas and collaboration opportunities.
            """)

def assign_theme_by_keywords(text: str) -> str:
    """Assign Babcock theme based on keyword matching"""
    text_lower = text.lower()
    theme_scores = {}
    
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        theme_scores[theme] = score
    
    if max(theme_scores.values()) > 0:
        return max(theme_scores, key=theme_scores.get)
    return "Uncategorized"

if __name__ == "__main__":
    main()