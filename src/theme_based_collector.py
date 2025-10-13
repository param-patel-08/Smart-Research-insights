"""
OpenAlex Collector with Theme-Based Filtering
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
import random
import logging

from config.themes import BABCOCK_THEMES
from config import settings as _settings

logger = logging.getLogger(__name__)


class ThemeBasedCollector:
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
            'User-Agent': f'BabcockResearchTrends/1.0 (mailto:{email})',
            'Accept': 'application/json'
        })
        self._last_request_ts = 0.0
        self._min_delay = 1.0
        
        logger.info("ThemeBasedCollector initialized")
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        logger.info(f"Using email: {email}")
    
    def build_theme_query(self, theme_name: str, top_n_keywords: int = 8) -> str:
        """
        Build OpenAlex search query from theme keywords
        Combined with domain context to ensure Babcock relevance
        
        Args:
            theme_name: Name of the Babcock theme
            top_n_keywords: Number of top keywords to use (too many = slow)
            
        Returns:
            Search query string ensuring technical/engineering context
        """
        theme_data = BABCOCK_THEMES[theme_name]
        theme_keywords = theme_data['keywords'][:top_n_keywords]
        
        # Babcock domain context - ensures technical/engineering focus
        # These terms filter out irrelevant academic areas (history, biology, social sciences)
        domain_context = [
            "engineering", "technology", "system", "design", "development",
            "application", "implementation", "analysis", "control", "detection",
            "sensor", "hardware", "software", "platform", "infrastructure",
            "architecture", "integration", "deployment", "operational"
        ]
        
        # Build query: (theme keywords) AND (domain context)
        # This ensures papers are about technical/engineering applications
        theme_query = ' '.join(theme_keywords)
        domain_query = ' '.join(domain_context[:8])  # Use subset to keep query manageable
        
        # Combined query ensures papers match theme AND are technical
        query = f"{theme_query} {domain_query}".strip()
        
        return query
    
    def _api_get(self, url: str, params: Dict, retries: int = 4) -> Optional[Dict]:
        for attempt in range(retries):
            now = time.time()
            delta = now - self._last_request_ts
            if delta < self._min_delay:
                wait = max(0.0, self._min_delay - delta) + random.uniform(0.0, 0.3)
                time.sleep(wait)
            try:
                resp = self.session.get(url, params=params, timeout=30)
                self._last_request_ts = time.time()
                resp.raise_for_status()
                return resp.json()
            except requests.HTTPError as exc:
                status = getattr(exc.response, 'status_code', None)
                if status in (403, 429) and attempt < retries - 1:
                    delay = max(1.0, 2 ** attempt)
                    # Adaptively increase base delay on throttling
                    self._min_delay = min(2.0, self._min_delay * 1.5)
                    time.sleep(delay)
                    continue
                return None
            except requests.RequestException:
                if attempt < retries - 1:
                    time.sleep(1.0)
                    continue
                return None
    
    def resolve_concept_ids_for_theme(self, theme_name: str) -> List[str]:
        """Resolve concept IDs from BABCOCK_THEMES[theme]['concept_names'] using OpenAlex /concepts.
        Returns a list of concept IDs like ["C41008148", ...]. Caches results per run.
        """
        # lightweight cache
        if not hasattr(self, "_concept_cache"):
            self._concept_cache = {}
        if theme_name in self._concept_cache:
            return self._concept_cache[theme_name]

        theme = BABCOCK_THEMES.get(theme_name, {})
        names = theme.get('concept_names', []) or []
        concept_ids: List[str] = []
        for name in names:
            params = {
                'search': name,
                'per-page': 5,
                'mailto': self.email,
                'select': 'id,display_name,level'
            }
            data = self._api_get('https://api.openalex.org/concepts', params)
            results = data.get('results', []) if data else []
            if results:
                # prefer the one whose display name closely matches
                best = None
                lname = name.lower()
                for it in results:
                    dn = (it.get('display_name') or '').lower()
                    if lname in dn or dn in lname:
                        best = it
                        break
                chosen = best or results[0]
                cid = chosen.get('id', '').split('/')[-1]
                if cid and cid.startswith('C'):
                    concept_ids.append(cid)
                    continue
            else:
                logger.warning(f"No concept results for '{name}'")
        self._concept_cache[theme_name] = concept_ids
        if concept_ids:
            logger.info(f"Resolved {len(concept_ids)} concepts for theme {theme_name}")
        return concept_ids

    def resolve_institution_ids(self, universities: Dict[str, str]) -> Dict[str, str]:
        """Resolve provided AU/NZ university names/ids to valid OpenAlex institution IDs.
        If a value already looks like an OpenAlex ID (starts with 'I'), keep it.
        Otherwise, search OpenAlex institutions API and pick the best match in AU/NZ.
        """
        resolved: Dict[str, str] = {}
        for name, maybe_id in universities.items():
            valid_id = None
            if isinstance(maybe_id, str) and maybe_id.startswith('I'):
                data = self._api_get(f'https://api.openalex.org/institutions/{maybe_id}', {
                    'select': 'id,display_name',
                    'mailto': self.email
                })
                if data and data.get('id'):
                    valid_id = maybe_id
            if not valid_id:
                variants = [name] + getattr(_settings, 'INSTITUTION_SYNONYMS', {}).get(name, [])
                lname = name.lower()
                # Try display_name.search for each variant
                for variant in variants:
                    params = {
                        'filter': f"display_name.search:{variant},country_code:AU|NZ",
                        'per-page': 5,
                        'mailto': self.email,
                        'select': 'id,display_name,country_code'
                    }
                    data = self._api_get('https://api.openalex.org/institutions', params)
                    items = data.get('results', []) if data else []
                    if items:
                        best = None
                        for it in items:
                            dn = (it.get('display_name') or '').lower()
                            if lname in dn or dn in lname or variant.lower() in dn:
                                best = it
                                break
                        chosen = best or items[0]
                        inst_id = chosen.get('id', '').split('/')[-1]
                        if inst_id:
                            valid_id = inst_id
                            logger.info(f"Resolved institution '{name}' via variant '{variant}' -> {inst_id}")
                            break
                # Fallback: generic search param
                if not valid_id:
                    for variant in variants:
                        params = {
                            'search': variant,
                            'filter': 'country_code:AU|NZ',
                            'per-page': 5,
                            'mailto': self.email,
                            'select': 'id,display_name,country_code'
                        }
                        data = self._api_get('https://api.openalex.org/institutions', params)
                        items = data.get('results', []) if data else []
                        if items:
                            best = None
                            for it in items:
                                dn = (it.get('display_name') or '').lower()
                                if lname in dn or dn in lname or variant.lower() in dn:
                                    best = it
                                    break
                            chosen = best or items[0]
                            inst_id = chosen.get('id', '').split('/')[-1]
                            if inst_id:
                                valid_id = inst_id
                                logger.info(f"Resolved institution '{name}' via search '{variant}' -> {inst_id}")
                                break
            if valid_id:
                resolved[name] = valid_id
            else:
                logger.warning(f"Could not resolve institution id for '{name}'")
        return resolved
    
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
        
        # Build theme query once
        keyword_query = self.build_theme_query(theme_name)
        logger.info(f"Keywords: {keyword_query[:100]}...")

        # Resolve AU/NZ institution IDs to ensure we can use institutions.id filter
        resolved_unis = self.resolve_institution_ids(universities)
        # Resolve concept IDs for this theme (optional)
        concept_ids = self.resolve_concept_ids_for_theme(theme_name)
        concept_filter = '|'.join(concept_ids) if concept_ids else None
        # Fetch per-university using institutions.id to avoid 403s on name search
        all_rows: List[Dict] = []
        for uni_name, uni_id in resolved_unis.items():
            rows = self._fetch_papers_for_uni(theme_name, keyword_query, uni_name, uni_id, max_papers, per_page, concept_filter)
            if rows:
                all_rows.extend(rows)
        logger.info(f"[OK] Fetched {len(all_rows)} papers for {theme_name}")
        return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()

    def _fetch_papers_for_uni(
        self,
        theme_name: str,
        keyword_query: str,
        uni_name: str,
        uni_id: Optional[str],
        max_papers: Optional[int],
        per_page: int,
        concept_filter: Optional[str] = None,
    ) -> List[Dict]:
        """Fetch papers for a single university using authorships.institutions.id with polite backoff retries."""
        collected: List[Dict] = []
        total = 0
        cursor = '*'
        drop_type_attempted = False
        type_filter_enabled = True
        while True:
            filters = [
                f"from_publication_date:{self.start_date.date().isoformat()}",
                f"to_publication_date:{self.end_date.date().isoformat()}",
                "is_paratext:false",
            ]
            if type_filter_enabled:
                filters.insert(2, "type:journal-article")
            if not uni_id:
                logger.warning(f"Skipping '{uni_name}' due to unresolved institution id")
                break
            # Prefer authorships.institutions.id as per docs (alias: institutions.id)
            filters.append(f"authorships.institutions.id:{uni_id}")
            if concept_filter:
                filters.append(f"concepts.id:{concept_filter}")

            params = {
                'filter': ','.join(filters),
                'per-page': min(per_page, 100),
                'cursor': cursor,
                'mailto': self.email,
                'select': 'id,type,title,abstract_inverted_index,publication_date,publication_year,authorships,primary_location,doi,cited_by_count,concepts',
                'sort': 'cited_by_count:desc'
            }
            # Only include free-text search when no concept filter is present (avoid over-constraining)
            if not concept_filter:
                params['search'] = keyword_query
            data = self._api_get(self.base_url, params)
            if not data:
                break
            results = data.get('results', [])
            if not results:
                if concept_filter:
                    concept_filter = None
                    cursor = '*'
                    continue
                # Final fallback: drop type filter and try once more
                if not drop_type_attempted:
                    drop_type_attempted = True
                    type_filter_enabled = False
                    cursor = '*'
                    continue
                break

            for work in results:
                paper = self._parse_work(work, theme_name, None)
                if paper:
                    # Force university attribution to the target AU/NZ uni
                    paper['university'] = uni_name
                    collected.append(paper)
                    total += 1
                    if max_papers and total >= max_papers:
                        break
            if max_papers and total >= max_papers:
                break

            cursor = data.get('meta', {}).get('next_cursor')
            if not cursor:
                break
            time.sleep(0.1)
        return collected
    
    def _parse_work(self, work: Dict, theme_name: str, id_to_name: Optional[Dict[str, str]] = None) -> Optional[Dict]:
        """Parse OpenAlex work into our format, preferring AU/NZ institutions that match provided IDs."""
        try:
            # Basic info
            openalex_id = work.get('id', '').split('/')[-1]
            title = work.get('title', '')
            if not title or not openalex_id:
                return None
            
            # Abstract
            abstract_inv = work.get('abstract_inverted_index')
            abstract = self._reconstruct_abstract(abstract_inv) if abstract_inv else None
            
            # Allow papers without abstracts for maximum recall
            # if not abstract or len(abstract) < 50:
            #     return None
            
            # Type (for post-filtering journals)
            wtype = work.get('type', '')
            
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
            
            # University: prefer institutions that match provided AU/NZ IDs
            university = ''
            matched = None
            if id_to_name:
                for authorship in authorships:
                    for inst in authorship.get('institutions', []):
                        inst_id_full = inst.get('id', '')
                        inst_id = inst_id_full.split('/')[-1] if inst_id_full else ''
                        if inst_id and inst_id in id_to_name:
                            matched = id_to_name[inst_id]
                            break
                    if matched:
                        break
            if matched:
                university = matched
            else:
                if authorships:
                    institutions = authorships[0].get('institutions', [])
                    if institutions:
                        university = institutions[0].get('display_name', '')
            
            # Journal and source type (to identify conferences)
            journal = None
            source_type = None  # Will be 'journal', 'conference', or other
            primary_location = work.get('primary_location', {})
            if primary_location:
                source = primary_location.get('source')
                if source:
                    journal = source.get('display_name')
                    source_type = source.get('type')  # Extract source type
            
            # Concepts (for verification)
            concepts = []
            for concept in work.get('concepts', []):
                concepts.append(concept.get('display_name'))
            
            # Calculate confidence score based on publication type, source type, and citations
            confidence = self._calculate_confidence(wtype, work.get('cited_by_count', 0), source_type)
            
            return {
                'openalex_id': openalex_id,
                'type': wtype or '',
                'source_type': source_type or '',  # NEW: journal/conference/other
                'title': title,
                'abstract': abstract or '',
                'date': pub_date.strftime('%Y-%m-%d'),
                'year': work.get('publication_year', pub_date.year),
                'authors': '; '.join(authors[:5]) if authors else '',
                'university': university or '',
                'journal': journal or '',
                'citations': work.get('cited_by_count', 0),
                'doi': work.get('doi', ''),
                'theme': theme_name,  # Pre-tagged with theme
                'concepts': '; '.join(concepts[:5]) if concepts else '',
                'confidence_score': confidence
            }
            
        except Exception as e:
            logger.debug(f"Error parsing work: {e}")
            return None
    
    def _calculate_confidence(self, pub_type: str, citations: int, source_type: str = None) -> float:
        """Calculate confidence score based on publication type, source type, and citation count.
        
        Confidence Levels:
        - 1.0: Journal articles with 5+ citations (high confidence)
        - 0.8: Journal articles with 1-4 citations, or conference papers with 3+ citations
        - 0.6: Conference papers with 1-2 citations, or recent journal articles (0 citations)
        - 0.4: Conference papers with 0 citations, working papers
        - 0.2: Preprints (not peer-reviewed)
        
        Note: source_type ('journal', 'conference') is more reliable than pub_type for distinguishing
        """
        pub_type_lower = pub_type.lower() if pub_type else ''
        source_type_lower = source_type.lower() if source_type else ''
        
        # Use source_type if available (more reliable)
        if source_type_lower == 'journal':
            # Journal articles
            if citations >= 5:
                return 1.0  # High confidence: established journal article
            elif citations >= 1:
                return 0.8  # Medium-high: cited journal article
            else:
                return 0.6  # Medium: recent journal article
        
        elif source_type_lower == 'conference':
            # Conference papers
            if citations >= 3:
                return 0.8  # Medium-high: well-cited conference paper
            elif citations >= 1:
                return 0.6  # Medium: cited conference paper
            else:
                return 0.4  # Medium-low: recent conference paper
        
        # Fallback to pub_type if source_type not available
        elif 'preprint' in pub_type_lower or 'arxiv' in pub_type_lower:
            return 0.2  # Low confidence: not peer-reviewed
        
        elif 'working' in pub_type_lower or 'report' in pub_type_lower:
            return 0.4  # Medium-low: preliminary work
        
        elif 'review' in pub_type_lower:
            # Review articles - treat like journal articles
            if citations >= 5:
                return 1.0
            elif citations >= 1:
                return 0.8
            else:
                return 0.6
        
        # Default for unknown types (likely journals based on OpenAlex data)
        else:
            if citations >= 5:
                return 0.8
            elif citations >= 1:
                return 0.6
            else:
                return 0.4
    
    def _reconstruct_abstract(self, inverted_index: Optional[Dict]) -> Optional[str]:
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
        
        themes_to_fetch = BABCOCK_THEMES.keys()
        if priority_only:
            themes_to_fetch = [
                name for name, data in BABCOCK_THEMES.items()
                if data['strategic_priority'] == 'HIGH'
            ]
        
        logger.info(f"\n{'='*80}")
        logger.info(f"FETCHING PAPERS FOR {len(themes_to_fetch)} THEMES")
        logger.info(f"{'='*80}\n")
        
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
        """Remove duplicate papers - LESS AGGRESSIVE: only exact DOI/ID matches."""
        if df.empty:
            return df
        before = len(df)
        
        # 1) Dedup by DOI (exact matches only)
        if 'doi' in df.columns:
            # Keep papers with non-empty DOIs, remove exact DOI duplicates
            df_with_doi = df[df['doi'].notna() & (df['doi'] != '')]
            df_without_doi = df[df['doi'].isna() | (df['doi'] == '')]
            
            if not df_with_doi.empty:
                df_with_doi = df_with_doi.sort_values(['doi', 'citations'], ascending=[True, False])
                df_with_doi = df_with_doi.drop_duplicates(subset=['doi'], keep='first')
            
            df = pd.concat([df_with_doi, df_without_doi], ignore_index=True)
        
        # 2) Dedup by OpenAlex ID (exact matches only)
        if 'openalex_id' in df.columns:
            df = df.drop_duplicates(subset=['openalex_id'], keep='first')
        
        # 3) REMOVED: No longer dedup by normalized title (too aggressive)
        #    Keep papers with similar titles as they may be different works
        
        removed = before - len(df)
        if removed > 0:
            logger.info(f"Deduplication: removed {removed} duplicates ({(removed/max(before,1)*100):.1f}%)")
        return df

    def filter_by_citations(self, df: pd.DataFrame, min_citations: int = 1) -> pd.DataFrame:
        """Keep only papers with cited_by_count >= min_citations."""
        if df.empty:
            return df
        before = len(df)
        df = df[df['citations'].fillna(0) >= min_citations]
        removed = before - len(df)
        if removed > 0:
            logger.info(f"Citation filter: removed {removed} papers with citations < {min_citations}")
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
    
    collector = ThemeBasedCollector(
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
