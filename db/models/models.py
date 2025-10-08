"""
Simplified database models for paper storage only
No ML/topic modeling - just paper metadata
"""
from datetime import datetime, date
from typing import List, Dict, Optional, Any
import json

from db.connection import get_db_cursor


class Paper:
    """Model for research papers from OpenAlex"""
    
    @staticmethod
    def insert(
        openalex_id: str,
        title: str,
        publication_date: date,
        year: int,
        abstract: Optional[str] = None,
        journal: Optional[str] = None,
        doi: Optional[str] = None,
        university: Optional[str] = None,
        concepts: Optional[List[Dict]] = None,
        primary_field: Optional[str] = None,
        is_open_access: bool = False
    ) -> str:
        """Insert a new paper or update if exists"""
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO papers (
                    openalex_id, title, abstract, publication_date, year,
                    journal, doi, university, concepts, primary_field,
                    is_open_access, last_synced
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (openalex_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    abstract = EXCLUDED.abstract,
                    publication_date = EXCLUDED.publication_date,
                    year = EXCLUDED.year,
                    journal = EXCLUDED.journal,
                    doi = EXCLUDED.doi,
                    university = EXCLUDED.university,
                    concepts = EXCLUDED.concepts,
                    primary_field = EXCLUDED.primary_field,
                    is_open_access = EXCLUDED.is_open_access,
                    last_synced = EXCLUDED.last_synced,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING openalex_id
            """, (
                openalex_id, title, abstract, publication_date, year,
                journal, doi, university,
                json.dumps(concepts) if concepts else None,
                primary_field, is_open_access,
                datetime.now()
            ))
            result = cur.fetchone()
            return result['openalex_id']
    
    @staticmethod
    def bulk_insert(papers: List[Dict[str, Any]]) -> int:
        """Bulk insert papers for efficiency"""
        if not papers:
            return 0
            
        with get_db_cursor() as cur:
            from psycopg2.extras import execute_values
            # Deduplicate incoming papers by openalex_id (keep first occurrence)
            seen = set()
            unique_papers = []
            for p in papers:
                oid = p.get('openalex_id')
                if not oid or oid in seen:
                    continue
                seen.add(oid)
                unique_papers.append(p)

            if not unique_papers:
                return 0

            # Insert in chunks to avoid massive single statements and
            # to reduce chance of duplicate-key collisions inside one batch
            CHUNK_SIZE = 500
            total_inserted = 0

            for i in range(0, len(unique_papers), CHUNK_SIZE):
                chunk = unique_papers[i:i+CHUNK_SIZE]

                values = []
                for paper in chunk:
                    values.append((
                        paper['openalex_id'],
                        paper['title'],
                        paper.get('abstract'),
                        paper['publication_date'],
                        paper['year'],
                        paper.get('journal'),
                        paper.get('doi'),
                        paper.get('university'),
                        json.dumps(paper.get('concepts')) if paper.get('concepts') else None,
                        paper.get('primary_field'),
                        paper.get('is_open_access', False),
                        datetime.now()
                    ))

                execute_values(
                    cur,
                    """
                    INSERT INTO papers (
                        openalex_id, title, abstract, publication_date, year,
                        journal, doi, university, concepts, primary_field,
                        is_open_access, last_synced
                    ) VALUES %s
                    ON CONFLICT (openalex_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        abstract = EXCLUDED.abstract,
                        publication_date = EXCLUDED.publication_date,
                        year = EXCLUDED.year,
                        journal = EXCLUDED.journal,
                        doi = EXCLUDED.doi,
                        university = EXCLUDED.university,
                        concepts = EXCLUDED.concepts,
                        primary_field = EXCLUDED.primary_field,
                        is_open_access = EXCLUDED.is_open_access,
                        last_synced = EXCLUDED.last_synced,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    values
                )

                total_inserted += len(chunk)

            return total_inserted
    
    @staticmethod
    def get_all(limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """Get all papers with optional pagination"""
        with get_db_cursor() as cur:
            query = """
                SELECT 
                    openalex_id, title, abstract, publication_date, year,
                    journal, doi, university, concepts, primary_field,
                    is_open_access, last_synced, created_at, updated_at
                FROM papers
                ORDER BY publication_date DESC
            """
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cur.execute(query)
            return cur.fetchall()
    
    @staticmethod
    def get_by_id(openalex_id: str) -> Optional[Dict]:
        """Get paper by OpenAlex ID (primary key)"""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM papers WHERE openalex_id = %s
            """, (openalex_id,))
            return cur.fetchone()
    
    @staticmethod
    def get_by_openalex_id(openalex_id: str) -> Optional[Dict]:
        """Get paper by OpenAlex ID"""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM papers WHERE openalex_id = %s
            """, (openalex_id,))
            return cur.fetchone()
    
    @staticmethod
    def search(
        keyword: Optional[str] = None,
        university: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Search papers with filters"""
        with get_db_cursor() as cur:
            query = "SELECT * FROM papers WHERE 1=1"
            params = []
            
            if keyword:
                query += " AND (title ILIKE %s OR abstract ILIKE %s)"
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            
            if university:
                query += " AND university ILIKE %s"
                params.append(f'%{university}%')
            
            if year_from:
                query += " AND year >= %s"
                params.append(year_from)
            
            if year_to:
                query += " AND year <= %s"
                params.append(year_to)
            
            query += " ORDER BY publication_date DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            return cur.fetchall()
    
    @staticmethod
    def count() -> int:
        """Get total paper count"""
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM papers")
            return cur.fetchone()['count']
    
    @staticmethod
    def delete(openalex_id: str) -> bool:
        """Delete a paper by OpenAlex ID"""
        with get_db_cursor() as cur:
            cur.execute("DELETE FROM papers WHERE openalex_id = %s", (openalex_id,))
            return cur.rowcount > 0


class IngestionState:
    """Track ingestion state and progress"""
    
    @staticmethod
    def get_latest(source: str = 'openalex') -> Optional[Dict]:
        """Get latest ingestion state"""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM ingestion_state
                WHERE source = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (source,))
            return cur.fetchone()
    
    @staticmethod
    def update(
        source: str,
        status: str,
        last_sync_date: Optional[datetime] = None,
        last_paper_date: Optional[date] = None,
        total_papers_fetched: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        """Update or insert ingestion state"""
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO ingestion_state (
                    source, last_sync_date, last_paper_date,
                    total_papers_fetched, status, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                source,
                last_sync_date or datetime.now(),
                last_paper_date,
                total_papers_fetched,
                status,
                json.dumps(metadata) if metadata else None
            ))


class IngestionLog:
    """Log each ingestion run"""
    
    @staticmethod
    def create(
        source: str,
        papers_added: int,
        papers_updated: int,
        papers_skipped: int,
        status: str,
        error_message: Optional[str] = None,
        query_params: Optional[Dict] = None,
        duration_seconds: Optional[int] = None
    ) -> int:
        """Create an ingestion log entry"""
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO ingestion_logs (
                    source, papers_added, papers_updated, papers_skipped,
                    status, error_message, query_params, duration_seconds
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                source, papers_added, papers_updated, papers_skipped,
                status, error_message,
                json.dumps(query_params) if query_params else None,
                duration_seconds
            ))
            return cur.fetchone()['id']
    
    @staticmethod
    def get_recent(limit: int = 10) -> List[Dict]:
        """Get recent ingestion logs"""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM ingestion_logs
                ORDER BY ingestion_date DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
