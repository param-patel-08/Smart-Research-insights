"""
OpenAlex Data Collector for Babcock Research Trends
Fetches research papers from Australasian universities
"""

import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import time
import logging
from tqdm import tqdm
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAlexCollector:
    """
    Collect research papers from OpenAlex API
    """
    
    def __init__(self, email: str, start_date: datetime, end_date: datetime):
        """
        Initialize collector
        
        Args:
            email: Email for polite pool access
            start_date: Start date for paper collection
            end_date: End date for paper collection
        """
        self.email = email
        self.start_date = start_date
        self.end_date = end_date
        self.base_url = "https://api.openalex.org/works"
        self.papers = []
        
        logger.info(f"OpenAlex Collector initialized")
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        logger.info(f"Using email: {email}")
    
    def fetch_papers_for_institution(self, 
                                     institution_name: str,
                                     institution_id: str,
                                     per_page: int = 200,
                                     max_results: int = None) -> List[Dict]:
        """
        Fetch papers from a specific institution
        
        Args:
            institution_name: Name of university
            institution_id: OpenAlex institution ID
            per_page: Results per page (max 200)
            max_results: Maximum papers to fetch (None = all)
            
        Returns:
            List of paper dictionaries
        """
        logger.info(f"\nFetching papers from: {institution_name}")
        
        papers = []
        page = 1
        total_fetched = 0
        
        # Format dates for OpenAlex API
        start_str = self.start_date.strftime("%Y-%m-%d")
        end_str = self.end_date.strftime("%Y-%m-%d")
        
        while True:
            # Build API query
            params = {
                'filter': f'institutions.id:{institution_id},from_publication_date:{start_str},to_publication_date:{end_str}',
                'per-page': per_page,
                'page': page,
                'mailto': self.email,
                'select': 'id,doi,title,publication_date,abstract_inverted_index,authorships,primary_location,concepts,cited_by_count'
            }
            
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    logger.info(f"  No more results at page {page}")
                    break
                
                # Process each paper
                for work in results:
                    paper = self._parse_paper(work, institution_name)
                    if paper:
                        papers.append(paper)
                        total_fetched += 1
                
                logger.info(f"  Page {page}: Fetched {len(results)} papers (Total: {total_fetched})")
                
                # Check if we've reached max results
                if max_results and total_fetched >= max_results:
                    logger.info(f"  Reached max results limit: {max_results}")
                    break
                
                # Check if there are more pages
                meta = data.get('meta', {})
                if page >= meta.get('count', 0) // per_page:
                    break
                
                page += 1
                
                # Rate limiting - be polite!
                time.sleep(0.1)  # 100ms delay between requests
                
            except requests.exceptions.RequestException as e:
                logger.error(f"  Error fetching page {page}: {e}")
                break
            except Exception as e:
                logger.error(f"  Unexpected error on page {page}: {e}")
                break
        
        logger.info(f"✓ Collected {len(papers)} papers from {institution_name}")
        return papers
    
    def _parse_paper(self, work: Dict, institution_name: str) -> Optional[Dict]:
        """
        Parse OpenAlex work object into paper dictionary
        
        Args:
            work: OpenAlex work object
            institution_name: Name of university
            
        Returns:
            Paper dictionary or None if parsing fails
        """
        try:
            # Extract title
            title = work.get('title', '').strip()
            if not title:
                return None
            
            # Extract abstract from inverted index
            abstract = self._reconstruct_abstract(work.get('abstract_inverted_index'))
            
            # Extract authors
            authors = []
            for authorship in work.get('authorships', []):
                author = authorship.get('author', {})
                display_name = author.get('display_name')
                if display_name:
                    authors.append(display_name)
            
            # Extract publication date
            pub_date = work.get('publication_date')
            if pub_date:
                try:
                    date = datetime.strptime(pub_date, "%Y-%m-%d")
                except:
                    date = None
            else:
                date = None
            
            # Extract URL
            url = work.get('id', '')  # OpenAlex ID
            doi = work.get('doi', '')
            
            # Extract keywords from concepts
            keywords = []
            for concept in work.get('concepts', [])[:10]:  # Top 10 concepts
                if concept.get('score', 0) > 0.3:  # Only high-confidence concepts
                    keywords.append(concept.get('display_name', ''))
            
            # Extract journal/venue
            primary_location = work.get('primary_location', {})
            source = primary_location.get('source', {})
            journal = source.get('display_name', '')
            
            # Citation count
            citations = work.get('cited_by_count', 0)
            
            return {
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'date': date,
                'university': institution_name,
                'url': url,
                'doi': doi,
                'keywords': keywords,
                'journal': journal,
                'citations': citations,
                'openalex_id': work.get('id', '')
            }
            
        except Exception as e:
            logger.debug(f"Error parsing paper: {e}")
            return None
    
    def _reconstruct_abstract(self, inverted_index: Optional[Dict]) -> str:
        """
        Reconstruct abstract from OpenAlex inverted index format
        
        Args:
            inverted_index: Dictionary mapping words to position indices
            
        Returns:
            Reconstructed abstract text
        """
        if not inverted_index:
            return ""
        
        try:
            # Create list of (position, word) tuples
            words_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    words_positions.append((pos, word))
            
            # Sort by position and join
            words_positions.sort(key=lambda x: x[0])
            abstract = ' '.join([word for pos, word in words_positions])
            
            return abstract
            
        except Exception as e:
            logger.debug(f"Error reconstructing abstract: {e}")
            return ""
    
    def fetch_all_universities(self, 
                              universities: Dict[str, str],
                              max_per_uni: int = None) -> pd.DataFrame:
        """
        Fetch papers from all specified universities
        
        Args:
            universities: Dict mapping university names to OpenAlex IDs
            max_per_uni: Max papers per university (None = all)
            
        Returns:
            DataFrame with all collected papers
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"COLLECTING PAPERS FROM {len(universities)} UNIVERSITIES")
        logger.info(f"{'='*80}\n")
        
        all_papers = []
        
        for uni_name, uni_id in tqdm(universities.items(), desc="Universities"):
            papers = self.fetch_papers_for_institution(
                uni_name, 
                uni_id,
                max_results=max_per_uni
            )
            all_papers.extend(papers)
            
            # Small delay between universities
            time.sleep(0.5)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_papers)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"COLLECTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Total papers collected: {len(df)}")
        logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
        logger.info(f"Universities: {df['university'].nunique()}")
        logger.info(f"Papers with abstracts: {df['abstract'].notna().sum()} ({df['abstract'].notna().sum()/len(df)*100:.1f}%)")
        
        return df
    
    def deduplicate_papers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate papers
        
        Args:
            df: DataFrame with papers
            
        Returns:
            Deduplicated DataFrame
        """
        original_count = len(df)
        
        # Remove by DOI first (most reliable)
        df = df[df['doi'].notna()]  # Keep only papers with DOIs
        df = df.drop_duplicates(subset=['doi'], keep='first')
        
        # Also check title similarity (case-insensitive)
        df['title_lower'] = df['title'].str.lower().str.strip()
        df = df.drop_duplicates(subset=['title_lower'], keep='first')
        df = df.drop(columns=['title_lower'])
        
        duplicates_removed = original_count - len(df)
        
        logger.info(f"\nDeduplication: Removed {duplicates_removed} duplicates ({duplicates_removed/original_count*100:.1f}%)")
        logger.info(f"Papers remaining: {len(df)}")
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filepath: str) -> None:
        """
        Save collected papers to CSV
        
        Args:
            df: DataFrame with papers
            filepath: Output file path
        """
        # Convert lists to JSON strings for CSV storage
        df_copy = df.copy()
        df_copy['authors'] = df_copy['authors'].apply(json.dumps)
        df_copy['keywords'] = df_copy['keywords'].apply(json.dumps)
        
        df_copy.to_csv(filepath, index=False)
        logger.info(f"\n✓ Saved {len(df)} papers to: {filepath}")
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict:
        """
        Get summary statistics of collected papers
        
        Args:
            df: DataFrame with papers
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_papers': len(df),
            'date_range': f"{df['date'].min()} to {df['date'].max()}",
            'universities_count': df['university'].nunique(),
            'papers_with_abstract': df['abstract'].notna().sum(),
            'abstract_percentage': df['abstract'].notna().sum() / len(df) * 100,
            'papers_per_university': df['university'].value_counts().to_dict(),
            'papers_per_year': df['date'].dt.year.value_counts().sort_index().to_dict(),
            'avg_citations': df['citations'].mean(),
            'total_unique_authors': len(set([author for authors in df['authors'] for author in authors]))
        }
        
        return stats


# ==================== USAGE EXAMPLE ====================

def main():
    """
    Example usage of OpenAlexCollector
    """
    from config.settings import (
        OPENALEX_EMAIL, 
        ANALYSIS_START_DATE, 
        ANALYSIS_END_DATE,
        ALL_UNIVERSITIES,
        RAW_PAPERS_CSV
    )
    
    # Initialize collector
    collector = OpenAlexCollector(
        email=OPENALEX_EMAIL,
        start_date=ANALYSIS_START_DATE,
        end_date=ANALYSIS_END_DATE
    )
    
    # For testing, fetch from just 3 universities first
    test_universities = dict(list(ALL_UNIVERSITIES.items())[:3])
    
    # Fetch papers (limit to 100 per university for testing)
    df = collector.fetch_all_universities(
        universities=test_universities,
        max_per_uni=100  # Remove this limit for full collection
    )
    
    # Deduplicate
    df = collector.deduplicate_papers(df)
    
    # Save to CSV
    collector.save_to_csv(df, RAW_PAPERS_CSV)
    
    # Print summary
    stats = collector.get_summary_stats(df)
    print("\n" + "="*80)
    print("COLLECTION SUMMARY")
    print("="*80)
    for key, value in stats.items():
        if key not in ['papers_per_university', 'papers_per_year']:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()