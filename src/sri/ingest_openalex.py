"""
OpenAlex ingestion with state tracking for incremental updates
Supports initial fetch (2019-present) and incremental updates
"""
import sys
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import requests
from tqdm import tqdm
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db.models.models import Paper, IngestionLog, IngestionState
from config.settings import OPENALEX_EMAIL, ALL_UNIVERSITIES


class OpenAlexIngester:
    """Ingest papers from OpenAlex API with incremental state tracking"""
    
    def __init__(self, email: str = OPENALEX_EMAIL):
        self.base_url = "https://api.openalex.org/works"
        self.email = email
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': f'ResearchInsights/1.0 (mailto:{email})'})
        self.source = 'openalex'
    
    def fetch_papers(
        self,
        institutions: List[str],
        start_date: date,
        end_date: date,
        per_page: int = 200,
        max_papers: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch papers from OpenAlex for given institutions and date range
        
        Args:
            institutions: List of OpenAlex institution IDs
            start_date: Start date for papers
            end_date: End date for papers
            per_page: Results per API page
            max_papers: Maximum papers to fetch (None for all)
            
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        # Build filters list
        filters = []
        
        # # Institution filter
        # institution_filter = '|'.join(institutions)
        # filters.append(f'institutions.id:{institution_filter}')
        
        # Date filter
        date_filter = f"from_publication_date:{start_date.isoformat()},to_publication_date:{end_date.isoformat()}"
        filters.append(date_filter)
        
        # Apply keyword search filter (MOST IMPORTANT!)
        from config.settings import QUERY_PARAMS
        if QUERY_PARAMS.get('search_keywords'):
            keywords = QUERY_PARAMS['search_keywords']
            filters.append(f'title_and_abstract.search:{keywords}')
            print(f"� Searching titles/abstracts for: {keywords[:100]}...")
        
        # Apply citation filter
        if QUERY_PARAMS.get('min_citations') and QUERY_PARAMS['min_citations'] > 0:
            filters.append(f"cited_by_count:>{QUERY_PARAMS['min_citations']}")
            print(f"📊 Filtering by minimum {QUERY_PARAMS['min_citations']} citations")
        
        # Apply open access filter
        if QUERY_PARAMS.get('open_access_only'):
            filters.append('is_oa:true')
            print(f"🔓 Filtering for open access only")
        
        # Apply journal filters
        if QUERY_PARAMS.get('journals'):
            journal_ids = '|'.join(QUERY_PARAMS['journals'])
            filters.append(f'primary_location.source.id:{journal_ids}')
            print(f"📖 Filtering by {len(QUERY_PARAMS['journals'])} specific journals")
        
        # Apply language filter
        if QUERY_PARAMS.get('languages'):
            lang_codes = '|'.join(QUERY_PARAMS['languages'])
            filters.append(f'language:{lang_codes}')
        
        # Apply country filter
        if QUERY_PARAMS.get('countries'):
            country_codes = '|'.join(QUERY_PARAMS['countries'])
            filters.append(f'authorships.institutions.country_code:{country_codes}')
        
        params = {
            'filter': ','.join(filters),
            'per-page': per_page,
            'cursor': '*',
            'mailto': self.email,
            'select': 'id,title,abstract_inverted_index,publication_date,publication_year,authorships,primary_location,doi,concepts,open_access'
        }
        
        print(f"Fetching papers from {start_date} to {end_date}")
        print(f"Institutions: {len(institutions)}")
        print(f"Filter: {params['filter']}")
        
        with tqdm(desc="Fetching papers") as pbar:
            while True:
                try:
                    # DEBUG: Print full URL on first request
                    if params['cursor'] == '*':
                        print(f"DEBUG - First request URL params: {params}")
                    
                    response = self.session.get(self.base_url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    
                    results = data.get('results', [])
                    if not results:
                        break
                    
                    for work in results:
                        paper = self._parse_paper(work)
                        if paper:
                            papers.append(paper)
                            pbar.update(1)
                        
                        if max_papers and len(papers) >= max_papers:
                            return papers
                    
                    # Get next cursor
                    meta = data.get('meta', {})
                    next_cursor = meta.get('next_cursor')
                    if not next_cursor:
                        break
                    
                    params['cursor'] = next_cursor
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                except requests.RequestException as e:
                    print(f"Error fetching papers: {e}")
                    break
        
        return papers
    
    def _parse_paper(self, work: Dict) -> Optional[Dict]:
        """Parse OpenAlex work into our paper format"""
        try:
            # Extract basic info
            openalex_id = work.get('id', '').split('/')[-1]
            if not openalex_id:
                return None
            
            title = work.get('title', '')
            if not title:
                return None
            
            # Parse abstract from inverted index
            abstract = self._reconstruct_abstract(work.get('abstract_inverted_index'))
            
            # Skip papers without abstracts
            if not abstract:
                return None
            
            # Parse date
            pub_date_str = work.get('publication_date')
            if pub_date_str:
                pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d').date()
            else:
                # Fallback to year
                year = work.get('publication_year')
                if year:
                    pub_date = date(year, 1, 1)
                else:
                    return None
            
            year = work.get('publication_year', pub_date.year)
            
            # Journal info
            journal = None
            primary_location = work.get('primary_location', {})
            if primary_location:
                source = primary_location.get('source')
                if source:
                    journal = source.get('display_name')
            
            # Get university (first institution)
            university = None
            authorships = work.get('authorships', [])
            if authorships:
                institutions = authorships[0].get('institutions', [])
                if institutions:
                    inst = institutions[0]
                    university = inst.get('display_name')
            
            # Parse concepts (research topics)
            concepts = []
            for concept in work.get('concepts', []):
                concepts.append({
                    'id': concept.get('id', '').split('/')[-1],
                    'display_name': concept.get('display_name'),
                    'level': concept.get('level', 0),
                    'score': concept.get('score', 0.0)
                })
            
            # Get primary field (highest level concept)
            primary_field = None
            if concepts:
                # Sort by level (descending) and score (descending)
                sorted_concepts = sorted(concepts, key=lambda x: (x['level'], x['score']), reverse=True)
                if sorted_concepts:
                    primary_field = sorted_concepts[0]['display_name']
            
            # Open access status
            open_access_obj = work.get('open_access', {})
            is_open_access = open_access_obj.get('is_oa', False) if open_access_obj else False
            
            return {
                'openalex_id': openalex_id,
                'title': title,
                'abstract': abstract,
                'publication_date': pub_date,
                'year': year,
                'journal': journal,
                'doi': work.get('doi'),
                'university': university,
                'concepts': concepts,
                'primary_field': primary_field,
                'is_open_access': is_open_access
            }
            
        except Exception as e:
            print(f"Error parsing paper: {e}")
            return None
    
    def _reconstruct_abstract(self, inverted_index: Optional[Dict]) -> Optional[str]:
        """Reconstruct abstract from OpenAlex inverted index"""
        if not inverted_index:
            return None
        
        try:
            # Create list of (position, word) tuples
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            
            # Sort by position and join
            word_positions.sort(key=lambda x: x[0])
            abstract = ' '.join(word for _, word in word_positions)
            return abstract
            
        except Exception:
            return None
    
    def ingest_initial(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """
        Initial ingestion from 2019-01-01 to today
        Now uses keyword search only (no institution filter)
        
        Args:
            start_date: Start date (defaults to 2019-01-01)
            end_date: End date (defaults to today)
            
        Returns:
            Dict with ingestion stats
        """
        if start_date is None:
            start_date = date(2019, 1, 1)
        if end_date is None:
            end_date = date.today()
        
        return self._run_ingestion(
            run_type='initial',
            institutions=[],  # No institution filter - using keyword search
            start_date=start_date,
            end_date=end_date
        )
    
    def ingest_incremental(self) -> Dict:
        """
        Incremental ingestion from last_fetched_date to today
        Now uses keyword search only (no institution filter)
        
        Returns:
            Dict with ingestion stats
        """
        # Get last fetched date
        last_fetched = IngestionState.get_last_fetched_date(self.source)
        if last_fetched is None:
            print("No previous ingestion found. Running initial ingestion.")
            return self.ingest_initial()
        
        # Fetch from day after last fetch to today
        start_date = last_fetched + timedelta(days=1)
        end_date = date.today()
        
        if start_date > end_date:
            print("Already up to date!")
            return {
                'status': 'completed',
                'papers_fetched': 0,
                'papers_inserted': 0,
                'message': 'Already up to date'
            }
        
        return self._run_ingestion(
            run_type='incremental',
            institutions=[],  # No institution filter - using keyword search
            start_date=start_date,
            end_date=end_date
        )
    
    def _run_ingestion(
        self,
        run_type: str,
        institutions: List[str],
        start_date: date,
        end_date: date,
        max_papers: Optional[int] = None
    ) -> Dict:
        """
        Run ingestion pipeline with state tracking
        
        Args:
            run_type: 'initial', 'incremental', or 'test'
            institutions: List of institution IDs
            start_date: Start date
            end_date: End date
            max_papers: Max papers to fetch (for testing)
            
        Returns:
            Dict with ingestion stats
        """
        start_time = time.time()
        
        try:
            # Fetch papers
            print(f"\nStarting {run_type} ingestion...")
            papers = self.fetch_papers(
                institutions=institutions,
                start_date=start_date,
                end_date=end_date,
                max_papers=max_papers
            )
            
            papers_fetched = len(papers)
            print(f"\nFetched {papers_fetched} papers")
            
            if papers_fetched == 0:
                # Still update state even if no papers
                IngestionState.update(
                    source=self.source,
                    status='completed',
                    last_sync_date=datetime.now(),
                    last_paper_date=end_date,
                    total_papers_fetched=0
                )
                
                # Log the run
                IngestionLog.create(
                    source=self.source,
                    papers_added=0,
                    papers_updated=0,
                    papers_skipped=0,
                    status='completed',
                    query_params={
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    duration_seconds=int(time.time() - start_time)
                )
                
                return {
                    'status': 'completed',
                    'papers_added': 0,
                    'papers_updated': 0
                }
            
            # Insert into database (upserts on conflict)
            print("Inserting papers into database...")
            papers_added = Paper.bulk_insert(papers)
            
            # Update ingestion state
            duration = int(time.time() - start_time)
            IngestionState.update(
                source=self.source,
                status='completed',
                last_sync_date=datetime.now(),
                last_paper_date=end_date,
                total_papers_fetched=papers_fetched,
                metadata={
                    'run_type': run_type,
                    'duration_seconds': duration
                }
            )
            
            # Log the run
            IngestionLog.create(
                source=self.source,
                papers_added=papers_added,
                papers_updated=0,
                papers_skipped=0,
                status='completed',
                query_params={
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'max_papers': max_papers
                },
                duration_seconds=duration
            )
            
            result = {
                'status': 'completed',
                'papers_added': papers_added,
                'papers_fetched': papers_fetched
            }
            
            print(f"\n✓ Ingestion completed successfully!")
            print(f"  Papers fetched: {papers_fetched}")
            print(f"  Papers added/updated: {papers_added}")
            print(f"  Duration: {duration}s")
            
            return result
            
        except Exception as e:
            # Log error
            duration = int(time.time() - start_time)
            IngestionLog.create(
                source=self.source,
                papers_added=0,
                papers_updated=0,
                papers_skipped=0,
                status='failed',
                error_message=str(e),
                duration_seconds=duration
            )
            
            print(f"\n✗ Ingestion failed: {e}")
            raise


def run_initial_ingestion():
    """Run initial ingestion from 2019-01-01 to today"""
    ingester = OpenAlexIngester()
    return ingester.ingest_initial()


def run_incremental_ingestion():
    """Run incremental ingestion from last fetch to today"""
    ingester = OpenAlexIngester()
    return ingester.ingest_incremental()


def run_test_ingestion(max_papers: int = 100):
    """Run test ingestion with limited papers"""
    ingester = OpenAlexIngester()
    return ingester._run_ingestion(
        run_type='test',
        institutions=[],  # No institution filter - using keyword search
        start_date=date(2024, 1, 1),
        end_date=date.today(),
        max_papers=max_papers
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest papers from OpenAlex into PostgreSQL')
    parser.add_argument(
        '--mode',
        choices=['initial', 'incremental', 'test'],
        default='initial',
        help='Ingestion mode'
    )
    parser.add_argument(
        '--max-papers',
        type=int,
        default=100,
        help='Max papers for test mode'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'initial':
        run_initial_ingestion()
    elif args.mode == 'incremental':
        run_incremental_ingestion()
    elif args.mode == 'test':
        run_test_ingestion(max_papers=args.max_papers)
