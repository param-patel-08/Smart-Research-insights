"""OpenAlex Data Collector for Babcock Research Trends."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


@dataclass
class InstitutionInfo:
    resolved_id: Optional[str]
    fallback_name: str

    def as_tuple(self) -> Tuple[Optional[str], str]:
        """Return legacy tuple representation (resolved_id, fallback_name)."""
        return self.resolved_id, self.fallback_name

    def __iter__(self):  # type: ignore[override]
        """Support unpacking for backwards compatibility."""
        yield self.resolved_id
        yield self.fallback_name


class OpenAlexCollector:
    """Collect research papers from the OpenAlex API with resiliency."""

    BASE_URL = "https://api.openalex.org/works"
    INSTITUTIONS_URL = "https://api.openalex.org/institutions"

    def __init__(self, email: str, start_date: datetime, end_date: datetime) -> None:
        self.email = email
        self.start_date = start_date
        self.end_date = end_date
        self._institution_cache: Dict[str, InstitutionInfo] = {}

        logger.info("OpenAlex Collector initialized")
        logger.info("Date range: %s to %s", start_date.date(), end_date.date())
        logger.info("Using email: %s", email)

    # ------------------------------------------------------------------
    # Institution resolution helpers
    # ------------------------------------------------------------------
    def resolve_institution(
        self, institution_name: str, institution_id: Optional[str]
    ) -> InstitutionInfo:
        """Resolve institution metadata (ID + best display name)."""

        if institution_name in self._institution_cache:
            return self._institution_cache[institution_name]

        resolved_id: Optional[str] = None
        fallback_name: str = institution_name

        if institution_id:
            validated = self._validate_institution_id(institution_id, institution_name)
            if validated.resolved_id:
                resolved_id = validated.resolved_id
            fallback_name = validated.fallback_name

        if not resolved_id:
            search_match = self._search_institution(institution_name)
            if search_match:
                resolved_id = search_match.get("id")
                fallback_name = search_match.get("display_name", fallback_name)

        if not resolved_id:
            logger.error("Unable to resolve institution id for %s", institution_name)

        info = InstitutionInfo(resolved_id=resolved_id, fallback_name=fallback_name)
        self._institution_cache[institution_name] = info
        return info

    def _validate_institution_id(self, institution_id: str, name: str) -> InstitutionInfo:
        try:
            resp = requests.get(
                f"{self.INSTITUTIONS_URL}/{institution_id}",
                params={"mailto": self.email},
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                resolved = data.get("id", "").split("/")[-1]
                display = data.get("display_name", name)
                if resolved:
                    return InstitutionInfo(resolved_id=resolved, fallback_name=display)
        except requests.exceptions.RequestException as exc:
            logger.warning("Failed validating institution %s (%s): %s", institution_id, name, exc)
        return InstitutionInfo(resolved_id=None, fallback_name=name)

    def _search_institution(self, name: str) -> Optional[Dict[str, str]]:
        for variant in self._generate_name_variants(name):
            try:
                resp = requests.get(
                    self.INSTITUTIONS_URL,
                    params={"search": variant, "per-page": 1, "mailto": self.email},
                    timeout=20,
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        item = results[0]
                        return {
                            "id": item.get("id", "").split("/")[-1],
                            "display_name": item.get("display_name", variant),
                        }
            except requests.exceptions.RequestException as exc:
                logger.warning("Institution search failed for %s: %s", variant, exc)
        return None

    def _generate_name_variants(self, name: str) -> Iterable[str]:
        name = name.strip()
        variants = {name}

        if not name.lower().startswith("the "):
            variants.add(f"The {name}")

        if name.lower().startswith("university of "):
            remainder = name[13:]
            variants.add(remainder)
            variants.add(f"The University of {remainder}")

        variants.add(name.replace("University", "Uni"))
        variants.add(name.replace(" of ", " "))

        return [v for v in variants if v]

    # ------------------------------------------------------------------
    # Collection entry points
    # ------------------------------------------------------------------
    def fetch_papers_for_institution(
        self,
        institution_name: str,
        institution_id: Optional[str],
        per_page: int = 200,
        max_results: Optional[int] = None,
    ) -> List[Dict]:
        """Fetch papers for a specific institution with fallback logic."""

        logger.info("\nFetching papers from: %s", institution_name)

        info = self.resolve_institution(institution_name, institution_id)

        if not info.resolved_id:
            logger.warning("Skipping %s: unresolved institution id", institution_name)
            # Still attempt fallback by display name
            tried_fallback = True
        else:
            tried_fallback = False

        start_str = self.start_date.strftime("%Y-%m-%d")
        end_str = self.end_date.strftime("%Y-%m-%d")

        papers: List[Dict] = []
        total_fetched = 0
        page = 1
        cursor: Optional[str] = "*"

        while True:
            filter_expr = self._build_filter(info, start_str, end_str, tried_fallback)
            params = {
                "filter": filter_expr,
                "per-page": per_page,
                "mailto": self.email,
                "select": "id,doi,title,publication_date,abstract_inverted_index,authorships,primary_location,concepts,cited_by_count",
                "sort": "publication_date:desc",
            }
            if cursor:
                params["cursor"] = cursor

            data = self._request_with_retry(params)
            if data is None:
                break

            results = data.get("results", [])
            if not results:
                if not tried_fallback:
                    logger.info("  No results with institutions.id. Trying display_name fallback")
                    tried_fallback = True
                    cursor = "*"
                    page = 1
                    continue
                logger.info("  No more results at page %s", page)
                break

            for work in results:
                paper = self._parse_paper(work, institution_name)
                if paper:
                    papers.append(paper)
                    total_fetched += 1

            logger.info("  Page %s: fetched %s papers (total %s)", page, len(results), total_fetched)

            if max_results and total_fetched >= max_results:
                logger.info("  Reached max results limit: %s", max_results)
                break

            meta = data.get("meta", {})
            cursor = meta.get("next_cursor")
            if not cursor:
                if not tried_fallback:
                    logger.info("  Exhausted id query. Switching to display_name fallback")
                    tried_fallback = True
                    cursor = "*"
                    page = 1
                    continue
                break

            page += 1
            time.sleep(0.1)

        logger.info("[OK] Collected %s papers from %s", len(papers), institution_name)
        return papers

    def fetch_all_universities(
        self, universities: Dict[str, str], max_per_uni: Optional[int] = None
    ) -> pd.DataFrame:
        logger.info("\n%s", "=" * 80)
        logger.info("COLLECTING PAPERS FROM %s UNIVERSITIES", len(universities))
        logger.info("%s\n", "=" * 80)

        all_papers: List[Dict] = []
        for name, openalex_id in tqdm(universities.items(), desc="Universities"):
            papers = self.fetch_papers_for_institution(name, openalex_id, max_results=max_per_uni)
            all_papers.extend(papers)
            time.sleep(0.5)

        df = pd.DataFrame(all_papers)
        if not df.empty:
            logger.info("Total papers collected: %s", len(df))
            logger.info("Date range: %s to %s", df["date"].min(), df["date"].max())
            logger.info("Universities: %s", df["university"].nunique())
            logger.info(
                "Papers with abstracts: %s (%.1f%%)",
                df["abstract"].notna().sum(),
                df["abstract"].notna().mean() * 100,
            )
        else:
            logger.warning("No papers collected. Check filters and network connectivity.")

        return df

    # ------------------------------------------------------------------
    # Networking helpers
    # ------------------------------------------------------------------
    def _build_filter(
        self,
        info: InstitutionInfo,
        start: str,
        end: str,
        use_fallback: bool,
    ) -> str:
        if not use_fallback and info.resolved_id:
            return f"institutions.id:{info.resolved_id},from_publication_date:{start},to_publication_date:{end}"
        fallback_name = info.fallback_name or ""
        return f"institutions.display_name.search:{fallback_name},from_publication_date:{start},to_publication_date:{end}"

    def _request_with_retry(self, params: Dict[str, str], max_attempts: int = 3) -> Optional[Dict]:
        attempt = 0
        backoff = 5
        while attempt < max_attempts:
            attempt += 1
            try:
                resp = requests.get(self.BASE_URL, params=params, timeout=30)
                if resp.status_code == 403:
                    logger.warning("  Received 403 from OpenAlex. Sleeping %ss (attempt %s/%s)", backoff, attempt, max_attempts)
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException as exc:
                logger.warning("  Request error (attempt %s/%s): %s", attempt, max_attempts, exc)
                time.sleep(backoff)
                backoff *= 2
        logger.error("  Failed to fetch data after %s attempts", max_attempts)
        return None

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    def _parse_paper(self, work: Dict, institution_name: str) -> Optional[Dict]:
        try:
            title = work.get("title", "").strip()
            if not title:
                return None

            abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))

            authors = []
            for authorship in work.get("authorships", []):
                author = authorship.get("author", {})
                name = author.get("display_name")
                if name:
                    authors.append(name)

            pub_date = work.get("publication_date")
            date_value: Optional[datetime] = None
            if pub_date:
                try:
                    date_value = datetime.strptime(pub_date, "%Y-%m-%d")
                except ValueError:
                    date_value = None

            primary_location = work.get("primary_location", {})
            journal = primary_location.get("source", {}).get("display_name", "")

            return {
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "date": date_value,
                "university": institution_name,
                "url": work.get("id", ""),
                "doi": work.get("doi", ""),
                "keywords": [c.get("display_name", "") for c in work.get("concepts", [])[:10]],
                "journal": journal,
                "citations": work.get("cited_by_count", 0),
                "openalex_id": work.get("id", ""),
            }
        except Exception as exc:  # defensive parsing
            logger.debug("Error parsing paper for %s: %s", institution_name, exc)
            return None

    def _reconstruct_abstract(self, inverted_index: Optional[Dict]) -> str:
        if not inverted_index:
            return ""
        try:
            words_positions = [
                (pos, word)
                for word, positions in inverted_index.items()
                for pos in positions
            ]
            words_positions.sort(key=lambda item: item[0])
            return " ".join(word for _, word in words_positions)
        except Exception as exc:
            logger.debug("Failed to reconstruct abstract: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def filter_by_cited_by_count(self, df: pd.DataFrame, min_citations: int) -> pd.DataFrame:
        original_count = len(df)
        df = df[df["citations"] >= min_citations]
        logger.info("Filtered papers with < %s citations: removed %s (%.1f%%)", min_citations, original_count - len(df), (original_count - len(df)) / max(original_count, 1) * 100)
        logger.info("Papers remaining: %s", len(df))
        return df
    
    def deduplicate_papers(self, df: pd.DataFrame) -> pd.DataFrame:
        original_count = len(df)

        df = df[df["doi"].notna()]
        df = df.drop_duplicates(subset=["doi"], keep="first")

        df["title_lower"] = df["title"].str.lower().str.strip()
        df = df.drop_duplicates(subset=["title_lower"], keep="first")
        df = df.drop(columns=["title_lower"])

        logger.info("Deduplication removed %s duplicates (%.1f%%)", original_count - len(df), (original_count - len(df)) / max(original_count, 1) * 100)
        logger.info("Papers remaining: %s", len(df))
        return df

    def save_to_csv(self, df: pd.DataFrame, filepath: str) -> None:
        df_copy = df.copy()
        df_copy["authors"] = df_copy["authors"].apply(json.dumps)
        df_copy["keywords"] = df_copy["keywords"].apply(json.dumps)
        df_copy.to_csv(filepath, index=False)
        logger.info("[OK] Saved %s papers to %s", len(df_copy), filepath)

    def get_summary_stats(self, df: pd.DataFrame) -> Dict:
        return {
            "total_papers": len(df),
            "date_range": f"{df['date'].min()} to {df['date'].max()}" if not df.empty else "N/A",
            "universities_count": df["university"].nunique() if not df.empty else 0,
            "papers_with_abstract": df["abstract"].notna().sum() if not df.empty else 0,
            "abstract_percentage": df["abstract"].notna().mean() * 100 if not df.empty else 0,
            "papers_per_university": df["university"].value_counts().to_dict() if not df.empty else {},
            "papers_per_year": df["date"].dt.year.value_counts().sort_index().to_dict() if not df.empty else {},
            "avg_citations": df["citations"].mean() if not df.empty else 0,
            "total_unique_authors": len({author for authors in df.get("authors", []) for author in authors}) if not df.empty else 0,
        }


def main() -> None:
    from config.settings import (
        ANALYSIS_END_DATE,
        ANALYSIS_START_DATE,
        ALL_UNIVERSITIES,
        OPENALEX_EMAIL,
        RAW_PAPERS_CSV,
    )

    collector = OpenAlexCollector(OPENALEX_EMAIL, ANALYSIS_START_DATE, ANALYSIS_END_DATE)
    sample_universities = dict(list(ALL_UNIVERSITIES.items())[:3])
    df = collector.fetch_all_universities(sample_universities, max_per_uni=20)
    df = collector.deduplicate_papers(df)
    df = collector.filter_by_cited_by_count(df, min_citations=1)
    collector.save_to_csv(df, RAW_PAPERS_CSV)
    stats = collector.get_summary_stats(df)
    logger.info("Summary: %s", stats)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
