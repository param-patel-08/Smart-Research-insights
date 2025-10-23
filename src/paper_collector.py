"""
OpenAlex Paper Collector with Theme-Based Filtering
Fetches papers matching Babcock's 9 strategic themes using keyword filters
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from tqdm import tqdm
import time
import logging

from config.themes import BABCOCK_THEMES
from config.settings import ALL_UNIVERSITIES

logger = logging.getLogger(__name__)


class PaperCollector:
    """
    Collect papers from OpenAlex filtered by Babcock theme keywords
    """
    
    def __init__(self, email: str, start_date: datetime, end_date: datetime):
        """
        Initialize collector
        
        Args:
            email: Your email for OpenAlex polite pool
            start_date: Start date for papers
            end_date: End date for papers
        """
        self.base_url = "https://api.openalex.org/works"
        self.email = email
        self.start_date = start_date
        self.end_date = end_date
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'BabcockResearchTrends/1.0 (mailto:{email})'
        })
        
        logger.info("ThemeBasedCollector initialized")
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        logger.info(f"Using email: {email}")
    
    def build_theme_query(self, theme_name: str, top_n_keywords: int = 30) -> str:
        """
        Build OpenAlex search query from theme keywords
        
        Args:
            theme_name: Name of the Babcock theme
            top_n_keywords: Number of top keywords to use (expanded for better coverage)
            
        Returns:
            Search query string for theme keywords
        """
        theme_data = BABCOCK_THEMES[theme_name]
        theme_keywords = theme_data['keywords'][:top_n_keywords]
        
        # Build query with just theme keywords
        # Relevance filtering will handle quality control after collection
        theme_query = ' OR '.join(theme_keywords)
        
        return theme_query
    
    def fetch_papers_for_theme(
        self,
        theme_name: str,
        universities: Dict[str, str],
        max_papers: Optional[int] = 500,
        per_page: int = 200
    ) -> pd.DataFrame:
        """
        Fetch papers for a specific theme from specified universities
        
        Args:
            theme_name: Babcock theme name
            universities: Dict of {university_name: openalex_id}
            max_papers: Maximum papers to fetch for this theme
            per_page: Results per page (max 200)
            
        Returns:
            DataFrame with papers
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"FETCHING PAPERS FOR THEME: {theme_name}")
        logger.info(f"{'='*80}")
        
        # Build filters
        filters = []
        
        # Date range
        filters.append(f"from_publication_date:{self.start_date.date().isoformat()}")
        filters.append(f"to_publication_date:{self.end_date.date().isoformat()}")
        
        # COUNTRY-BASED FILTER: All Australian and New Zealand institutions
        # This is more reliable than specific institution IDs because:
        # 1. OpenAlex provides accurate institution names automatically
        # 2. Captures all AU/NZ research institutions
        # 3. Simpler and more maintainable
        # Post-processing will filter to major universities only
        filters.append(f"institutions.country_code:AU|NZ")
        
        # USE ONLY OPENALEX CONCEPTS - NO KEYWORD SEARCH
        # Concepts are more reliable and accurately categorized by OpenAlex
        # NOTE: Use specific concepts to minimize overlap while ensuring coverage
        concept_mapping = {
            'AI_Machine_Learning': 'C154945302|C119857082',  # AI | ML 
            'Defense_Security': 'C2780653162|C149923435',  # Security engineering | National security
            'Autonomous_Systems': 'C50522688|C154945302',  # Robotics | Autonomous agents
            'Cybersecurity': 'C2778793908|C554061246|C199360897|C17744445',  # Computer security | Cybersecurity | Information security | Cryptography
            'Energy_Sustainability': 'C2778407487|C39432304',  # Renewable energy | Environmental science
            'Advanced_Manufacturing': 'C2778455934|C175444787|C74650414',  # Manufacturing | Additive manufacturing | Industrial engineering
            'Marine_Naval': 'C153294291|C205649164',  # Ocean engineering | Marine engineering  
            'Space_Aerospace': 'C152322641|C145342643|C166957645',  # Aerospace engineering | Astronautics | Space exploration
            'Digital_Transformation': 'C41008148|C2777956493|C138885662'  # Computer Science | Business | Information systems
        }
        
        # Add concept filter - REQUIRED for all themes
        if theme_name not in concept_mapping:
            logger.warning(f"No concept mapping for theme: {theme_name}")
            return pd.DataFrame()
        
        filters.append(f"concepts.id:{concept_mapping[theme_name]}")
        logger.info(f"Using concept-based filtering (no keyword search)")
        
        # Build request params
        # NO search parameter - we rely on concepts + relevance scoring instead
        params = {
            'filter': ','.join(filters),
            'per-page': per_page,
            'cursor': '*',
            'mailto': self.email,
            'select': 'id,title,abstract_inverted_index,publication_date,publication_year,authorships,primary_location,doi,cited_by_count,concepts'
        }
        
        papers = []
        total_fetched = 0
        
        try:
            with tqdm(desc=f"Fetching {theme_name}", unit="papers") as pbar:
                while True:
                    response = self.session.get(self.base_url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    
                    results = data.get('results', [])
                    if not results:
                        break
                    
                    for work in results:
                        paper = self._parse_work(work, theme_name)
                        if paper:
                            papers.append(paper)
                            pbar.update(1)
                            total_fetched += 1
                            
                            if max_papers and total_fetched >= max_papers:
                                logger.info(f"  Reached limit of {max_papers} papers")
                                break
                    
                    if max_papers and total_fetched >= max_papers:
                        break
                    
                    # Get next cursor
                    meta = data.get('meta', {})
                    next_cursor = meta.get('next_cursor')
                    if not next_cursor:
                        break
                    
                    params['cursor'] = next_cursor
                    time.sleep(0.1)  # Rate limiting
                    
        except requests.RequestException as e:
            logger.error(f"Error fetching {theme_name}: {e}")
        
        logger.info(f"[OK] Fetched {len(papers)} papers for {theme_name}")
        
        return pd.DataFrame(papers) if papers else pd.DataFrame()
    
    def _parse_work(self, work: Dict, theme_name: str) -> Optional[Dict]:
        """Parse OpenAlex work into our format"""
        try:
            # Basic info
            openalex_id = work.get('id', '').split('/')[-1]
            title = work.get('title', '')
            if not title or not openalex_id:
                return None
            
            # Abstract
            abstract_inv = work.get('abstract_inverted_index')
            abstract = self._reconstruct_abstract(abstract_inv) if abstract_inv else None
            
            if not abstract or len(abstract) < 50:
                return None  # Skip papers without meaningful abstracts
            
            # Date
            pub_date_str = work.get('publication_date')
            if pub_date_str:
                pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d')
            else:
                year = work.get('publication_year')
                if year:
                    pub_date = datetime(year, 1, 1)
                else:
                    return None
            
            # Authors
            authors = []
            authorships = work.get('authorships', [])
            for authorship in authorships:
                author = authorship.get('author', {})
                name = author.get('display_name')
                if name:
                    authors.append(name)
            
            # University - Extract AU/NZ institution from authorships
            # Papers are filtered by country code (AU|NZ), so every paper has AU/NZ author
            # OpenAlex provides institution name directly in authorship data
            from config.settings import ALL_UNIVERSITIES
            
            university = None
            
            # Search through ALL authorships for AU/NZ institution (country code AU or NZ)
            for authorship in authorships:
                institutions = authorship.get('institutions', [])
                for inst in institutions:
                    country = inst.get('country_code', '')
                    if country in ['AU', 'NZ']:
                        # Found AU/NZ institution - use OpenAlex display name
                        university = inst.get('display_name', '')
                        break
                if university:
                    break
            
            # Fallback: use first author's first institution if no AU/NZ found
            if not university and authorships:
                institutions = authorships[0].get('institutions', [])
                if institutions:
                    university = institutions[0].get('display_name', 'Unknown')
            
            # Journal
            journal = None
            primary_location = work.get('primary_location', {})
            if primary_location:
                source = primary_location.get('source')
                if source:
                    journal = source.get('display_name')
            
            # Concepts (for verification)
            concepts = []
            for concept in work.get('concepts', []):
                concepts.append(concept.get('display_name'))
            
            return {
                'openalex_id': openalex_id,
                'title': title,
                'abstract': abstract,
                'date': pub_date.strftime('%Y-%m-%d'),
                'year': work.get('publication_year', pub_date.year),
                'authors': '; '.join(authors[:5]) if authors else '',
                'university': university or '',
                'journal': journal or '',
                'citations': work.get('cited_by_count', 0),
                'doi': work.get('doi', ''),
                'theme': theme_name,  # Pre-tagged with theme
                'concepts': '; '.join(concepts[:5]) if concepts else ''
            }
            
        except Exception as e:
            logger.debug(f"Error parsing work: {e}")
            return None
    
    def _reconstruct_abstract(self, inverted_index: Dict) -> Optional[str]:
        """Reconstruct abstract from OpenAlex inverted index"""
        try:
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            
            word_positions.sort(key=lambda x: x[0])
            abstract = ' '.join(word for _, word in word_positions)
            return abstract
        except Exception:
            return None
    
    def calculate_relevance_score(self, paper: Dict, theme_name: str) -> float:
        """
        Calculate Babcock-specific relevance score for a paper
        
        Checks for:
        1. Theme keyword matches in title/abstract
        2. Technical/engineering context
        3. Application domain (naval, defense, etc.)
        
        Returns:
            Score from 0.0 (irrelevant) to 1.0 (highly relevant)
        """
        theme_data = BABCOCK_THEMES[theme_name]
        keywords = [kw.lower() for kw in theme_data['keywords']]
        
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        concepts = paper.get('concepts', '').lower()
        
        score = 0.0
        
        # 1. Theme keyword matches (40% weight)
        keyword_matches = sum(1 for kw in keywords if kw in text)
        keyword_score = min(keyword_matches / 3, 1.0)  # 3+ matches = full score
        score += keyword_score * 0.4
        
        # 2. Technical context words (30% weight)
        technical_terms = [
            'system', 'design', 'technology', 'engineering', 'development',
            'implementation', 'analysis', 'control', 'detection', 'sensor',
            'platform', 'architecture', 'operational', 'performance'
        ]
        tech_matches = sum(1 for term in technical_terms if term in text)
        tech_score = min(tech_matches / 4, 1.0)  # 4+ matches = full score
        score += tech_score * 0.3
        
        # 3. Babcock domain indicators (30% weight)
        domain_indicators = [
            'naval', 'maritime', 'defense', 'defence', 'military', 'autonomous',
            'marine', 'aerospace', 'security', 'cyber', 'energy', 'manufacturing',
            'digital', 'innovation', 'capability'
        ]
        domain_matches = sum(1 for term in domain_indicators if term in text or term in concepts)
        domain_score = min(domain_matches / 2, 1.0)  # 2+ matches = full score
        score += domain_score * 0.3
        
        return round(score, 3)
    
    def filter_by_relevance(self, df: pd.DataFrame, min_score: float = 0.2) -> pd.DataFrame:
        """
        Filter papers by Babcock relevance score
        
        Args:
            df: DataFrame with papers
            min_score: Minimum relevance score (0.0-1.0)
            
        Returns:
            Filtered DataFrame with relevance scores
        """
        if df.empty:
            return df
        
        logger.info(f"\nCalculating Babcock relevance scores...")
        
        scores = []
        for _, paper in df.iterrows():
            score = self.calculate_relevance_score(paper.to_dict(), paper['theme'])
            scores.append(score)
        
        df['relevance_score'] = scores
        
        before = len(df)
        df = df[df['relevance_score'] >= min_score]
        after = len(df)
        
        logger.info(f"Relevance filtering: {before} -> {after} papers (kept {after/before*100:.1f}%)")
        logger.info(f"  Threshold: {min_score}")
        logger.info(f"  Mean score: {df['relevance_score'].mean():.3f}")
        logger.info(f"  Min score: {df['relevance_score'].min():.3f}")
        logger.info(f"  Max score: {df['relevance_score'].max():.3f}")
        
        return df
    
    def fetch_all_themes(
        self,
        universities: Dict[str, str],
        max_per_theme: Optional[int] = 500,
        priority_only: bool = False,
        min_relevance: float = 0.5
    ) -> pd.DataFrame:
        """
        Fetch papers for all Babcock themes with relevance filtering
        
        Args:
            universities: Dict of {university_name: openalex_id}
            max_per_theme: Max papers per theme
            priority_only: If True, only fetch HIGH priority themes
            min_relevance: Minimum Babcock relevance score (0.0-1.0)
            
        Returns:
            Combined DataFrame with relevant theme papers
        """
        all_papers = []
        
        themes_to_fetch = list(BABCOCK_THEMES.keys())
        if priority_only:
            themes_to_fetch = [
                name for name, data in BABCOCK_THEMES.items()
                if data['strategic_priority'] == 'HIGH'
            ]
        
        # IMPORTANT: Fetch AI/ML first to avoid it being captured by other themes
        # AI/ML papers often overlap with Autonomous, Defense, Cybersecurity
        # By fetching AI/ML first, we ensure proper categorization
        if 'AI_Machine_Learning' in themes_to_fetch:
            themes_to_fetch.remove('AI_Machine_Learning')
            themes_to_fetch.insert(0, 'AI_Machine_Learning')
        
        logger.info(f"\n{'='*80}")
        logger.info(f"FETCHING PAPERS FOR {len(themes_to_fetch)} THEMES")
        logger.info(f"{'='*80}\n")
        logger.info(f"Fetch order: {', '.join(themes_to_fetch)}\n")
        
        for theme_name in themes_to_fetch:
            df_theme = self.fetch_papers_for_theme(
                theme_name,
                universities,
                max_papers=max_per_theme
            )
            
            if not df_theme.empty:
                all_papers.append(df_theme)
            
            time.sleep(0.5)  # Be nice to OpenAlex
        
        if all_papers:
            combined_df = pd.concat(all_papers, ignore_index=True)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"INITIAL COLLECTION COMPLETE")
            logger.info(f"{'='*80}")
            logger.info(f"Total papers collected: {len(combined_df)}")
            
            # Apply Babcock relevance filtering
            combined_df = self.filter_by_relevance(combined_df, min_score=min_relevance)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"FINAL COLLECTION (BABCOCK-RELEVANT ONLY)")
            logger.info(f"{'='*80}")
            logger.info(f"Total papers: {len(combined_df)}")
            logger.info(f"Themes covered: {combined_df['theme'].nunique()}")
            logger.info(f"Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
            
            # Show distribution
            logger.info("\nPapers by theme (Babcock-relevant):")
            for theme, count in combined_df['theme'].value_counts().items():
                avg_score = combined_df[combined_df['theme'] == theme]['relevance_score'].mean()
                logger.info(f"  {theme}: {count} papers (avg relevance: {avg_score:.3f})")
            
            return combined_df
        else:
            logger.warning("No papers collected!")
            return pd.DataFrame()
    
    def deduplicate_papers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate papers"""
        before = len(df)
        df = df.drop_duplicates(subset=['openalex_id'])
        after = len(df)
        
        if before > after:
            logger.info(f"Deduplication: Removed {before - after} duplicates ({(before-after)/before*100:.1f}%)")
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filepath: str):
        """Save papers to CSV"""
        df.to_csv(filepath, index=False)
        logger.info(f"[OK] Saved {len(df)} papers to: {filepath}")


if __name__ == "__main__":
    # Quick test
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from config.settings import OPENALEX_EMAIL, ALL_UNIVERSITIES, ANALYSIS_START_DATE, ANALYSIS_END_DATE
    
    collector = PaperCollector(
        email=OPENALEX_EMAIL,
        start_date=ANALYSIS_START_DATE,
        end_date=ANALYSIS_END_DATE
    )
    
    # Test with 3 universities, HIGH priority themes only
    test_unis = dict(list(ALL_UNIVERSITIES.items())[:3])
    
    df = collector.fetch_all_themes(
        universities=test_unis,
        max_per_theme=100,
        priority_only=True,  # Only fetch HIGH priority themes
        min_relevance=0.5    # Minimum 50% relevance to Babcock domains
    )
    
    df = collector.deduplicate_papers(df)
    collector.save_to_csv(df, 'data/raw/papers_theme_filtered.csv')
    
    print(f"\n{'='*80}")
    print(f"✓ Collected {len(df)} Babcock-relevant papers!")
    print(f"{'='*80}")
    print(f"\nSample papers:")
    for i, row in df.head(3).iterrows():
        print(f"\n{i+1}. {row['title'][:80]}...")
        print(f"   Theme: {row['theme']}")
        print(f"   Relevance: {row['relevance_score']:.3f}")
        print(f"   Concepts: {row['concepts'][:100]}...")
