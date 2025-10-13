"""
BABCOCK RESEARCH TRENDS - FULL ANALYSIS PIPELINE
Run this script to execute the complete analysis from start to finish
"""

import sys
import os
from datetime import datetime
import logging

# Setup logging
log_file = f'logs/full_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def print_banner(text):
    """Print a nice banner"""
    print("\n" + "="*80)
    print("  RESEARCH TREND ANALYZER - FULL ANALYSIS")
    print("="*80 + "\n")


def run_step(step_name, function, *args, **kwargs):
    """Run a pipeline step with error handling"""
    print_banner(f"STEP: {step_name}")
    
    start_time = datetime.now()
    
    try:
        result = function(*args, **kwargs)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[OK] {step_name} completed in {elapsed:.1f} seconds")
        return result, True
        
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"[ERROR] {step_name} failed after {elapsed:.1f} seconds: {e}")
        import traceback
        traceback.print_exc()
        return None, False


def main():
    """
    Run complete analysis pipeline
    """
    print_banner("BABCOCK RESEARCH TRENDS - FULL ANALYSIS")
    
    logger.info(f"Analysis started at: {datetime.now()}")
    logger.info(f"Log file: {log_file}")
    
    overall_start = datetime.now()
    
    # Import configurations
    from config.settings import (
        OPENALEX_EMAIL,
        ALL_UNIVERSITIES,
        ANALYSIS_START_DATE,
        ANALYSIS_END_DATE,
        RAW_PAPERS_CSV,
        METADATA_CSV,
        EMBEDDINGS_PATH,
        BERTOPIC_MODEL_PATH,
        PROCESSED_PAPERS_CSV,
        TOPICS_OVER_TIME_CSV,
        TOPIC_MAPPING_PATH,
        TREND_ANALYSIS_PATH,
        NR_TIME_BINS,
        MIN_RELEVANCE_SCORE,
        MIN_ABSTRACT_LENGTH
    )
    from config.themes import BABCOCK_THEMES
    
    # Print configuration
    logger.info("\n" + "="*80)
    logger.info("CONFIGURATION")
    logger.info(f"Email: {OPENALEX_EMAIL}")
    logger.info(f"Date range: {ANALYSIS_START_DATE.date()} to {ANALYSIS_END_DATE.date()}")
    logger.info(f"Universities: {len(ALL_UNIVERSITIES)}")
    logger.info(f"Themes: {len(BABCOCK_THEMES)}")
    logger.info(f"Theme-based filtering: ENABLED (with relevance scoring)")
    logger.info(f"Minimum relevance threshold: 0.2 (20% theme-specific)")
    
    # Ask user for data collection scope
    print("\n" + "="*80)
    print("DATA COLLECTION SCOPE")
    print("="*80)
    print("\nOptions:")
    print("  1. Quick test (3 universities, 100 papers each) - 5 minutes")
    print("  2. Medium test (10 universities, 500 papers each) - 15 minutes")
    print("  3. Full collection (all 44 universities, no limit) - 30-60 minutes")
    
    # Check for command line argument
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        print(f"\nUsing command line choice: {choice}")
    else:
        choice = input("\nEnter your choice (1/2/3) [default: 1]: ").strip() or "1"
    
    if choice == "1":
        test_universities = dict(list(ALL_UNIVERSITIES.items())[:3])
        max_per_uni = 100
        logger.info("Mode: Quick test")
    elif choice == "2":
        test_universities = dict(list(ALL_UNIVERSITIES.items())[:10])
        max_per_uni = 500
        logger.info("Mode: Medium test")
    else:
        test_universities = ALL_UNIVERSITIES
        max_per_uni = None
        logger.info("Mode: Full collection")
    
    # ==================== STEP 1: DATA COLLECTION ====================
    
    def step1_collect():
        from src.theme_based_collector import ThemeBasedCollector
        
        collector = ThemeBasedCollector(
            email=OPENALEX_EMAIL,
            start_date=ANALYSIS_START_DATE,
            end_date=ANALYSIS_END_DATE
        )
        
        # Map collection scope to theme parameters
        if choice == "1":  # Quick test
            max_per_theme = 50
            priority_only = True  # Only HIGH priority themes
        elif choice == "2":  # Medium test
            max_per_theme = 100
            priority_only = True
        else:  # Full collection
            max_per_theme = None  # Unlimited per theme
            priority_only = False  # All 9 themes
        
        # Fetch theme-filtered papers with relevance scoring
        logger.info(f"Fetching papers with theme-based filtering (priority_only={priority_only})")
        df = collector.fetch_all_themes(
            universities=test_universities,
            max_per_theme=max_per_theme,
            priority_only=priority_only,
            min_relevance=0.1  # Filter out completely irrelevant papers (was 0.0)
        )

        # University filtering already done by collector - no need to re-filter
        # The collector only fetches from the specified universities
        logger.info(f"\nPapers collected from {df['university'].nunique()} universities")
        
        # Filter out papers with very low relevance (misclassified papers)
        if not df.empty and 'relevance_score' in df.columns:
            before_filter = len(df)
            df = df[df['relevance_score'] >= 0.1]  # Remove papers with <10% relevance
            removed = before_filter - len(df)
            if removed > 0:
                logger.info(f"Filtered out {removed} papers with relevance < 0.1 (misclassified)")
        
        # Include all publication types (journals, conferences, preprints, working papers)
        # Confidence scores assigned based on type + citations
        # No type filtering - let confidence scores handle quality weighting
        
        # Option A: Remove citation filter for maximum recall
        # df = collector.filter_by_citations(df, min_citations=1)
        
        # Remove duplicates
        if not df.empty:
            df = collector.deduplicate_papers(df)

        # Early guard: stop pipeline if nothing to preprocess
        if df.empty:
            logger.error("No papers collected after AU+NZ filters. Check institution resolution or expand date range.")
            raise RuntimeError("No papers collected to preprocess")
        
        # Log confidence score distribution
        if 'confidence_score' in df.columns:
            logger.info("\nConfidence Score Distribution:")
            logger.info(f"  High (1.0):        {(df['confidence_score'] == 1.0).sum()} papers ({(df['confidence_score'] == 1.0).sum() / len(df) * 100:.1f}%)")
            logger.info(f"  Medium-High (0.8): {(df['confidence_score'] == 0.8).sum()} papers ({(df['confidence_score'] == 0.8).sum() / len(df) * 100:.1f}%)")
            logger.info(f"  Medium (0.6):      {(df['confidence_score'] == 0.6).sum()} papers ({(df['confidence_score'] == 0.6).sum() / len(df) * 100:.1f}%)")
            logger.info(f"  Medium-Low (0.4):  {(df['confidence_score'] == 0.4).sum()} papers ({(df['confidence_score'] == 0.4).sum() / len(df) * 100:.1f}%)")
            logger.info(f"  Low (0.2):         {(df['confidence_score'] == 0.2).sum()} papers ({(df['confidence_score'] == 0.2).sum() / len(df) * 100:.1f}%)")
            logger.info(f"  Mean confidence: {df['confidence_score'].mean():.2f}")
        
        # Log publication type distribution
        if 'type' in df.columns:
            logger.info("\nPublication Type Distribution:")
            type_counts = df['type'].value_counts()
            for pub_type, count in type_counts.items():
                logger.info(f"  {pub_type}: {count} papers ({count / len(df) * 100:.1f}%)")
        
        # Save raw collection snapshot
        collector.save_to_csv(df, RAW_PAPERS_CSV)
        
        logger.info(f"\nCollected {len(df)} papers across all publication types (AU+NZ only)")
        logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
        return df
    
    df_raw, success = run_step("1. DATA COLLECTION", step1_collect)
    if not success:
        logger.error("Pipeline stopped due to data collection failure")
        return
    
    # ==================== STEP 2: PREPROCESSING ====================
    
    def step2_preprocess():
        import pandas as pd
        from src.paper_preprocessor import PaperPreprocessor
        
        df = pd.read_csv(RAW_PAPERS_CSV)
        
        preprocessor = PaperPreprocessor(
            min_abstract_length=MIN_ABSTRACT_LENGTH
        )
        
        df = preprocessor.preprocess_abstracts(df)
        
        # Prepare documents and metadata for BERTopic
        documents = df['processed_text'].tolist()
        metadata = df[['title', 'university', 'date', 'authors', 'journal', 'citations']].copy()
        
        # Save
        metadata.to_csv(METADATA_CSV, index=False)
        
        documents_file = METADATA_CSV.replace('metadata.csv', 'documents.txt')
        with open(documents_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(documents))
        
        return (documents, metadata)
    
    result, success = run_step("2. PREPROCESSING", step2_preprocess)
    if not success:
        logger.error("Pipeline stopped due to preprocessing failure")
        return
    
    documents, metadata = result
    
    # ==================== STEP 3: TOPIC MODELING ====================
    
    def step3_topic_modeling():
        import pandas as pd
        from src.topic_analyzer import BabcockTopicAnalyzer
        
        # Load documents
        documents_file = METADATA_CSV.replace('metadata.csv', 'documents.txt')
        with open(documents_file, 'r', encoding='utf-8') as f:
            documents = [line.strip() for line in f if line.strip()]
        
        metadata = pd.read_csv(METADATA_CSV)
        timestamps = pd.to_datetime(metadata['date']).tolist()
        
        # Train model (use config params for smaller datasets)
        from config.settings import TOPIC_MODEL_PARAMS
        analyzer = BabcockTopicAnalyzer(
            min_topic_size=TOPIC_MODEL_PARAMS['min_topic_size'],
            nr_topics=30  # Reduced from 60 for smaller dataset (133 papers)
        )
        topics, probs = analyzer.fit_transform(documents, embeddings_path=EMBEDDINGS_PATH)
        
        # Temporal analysis
        topics_over_time = analyzer.get_topics_over_time(
            documents, timestamps, topics, nr_bins=NR_TIME_BINS
        )
        
        # Save
        analyzer.save_model(BERTOPIC_MODEL_PATH)
        
        metadata['topic_id'] = topics
        metadata['topic_probability'] = [p.max() if len(p) > 0 else 0 for p in probs]
        metadata.to_csv(PROCESSED_PAPERS_CSV, index=False)
        
        topics_over_time.to_csv(TOPICS_OVER_TIME_CSV, index=False)
        
        return analyzer
    
    analyzer, success = run_step("3. TOPIC MODELING (BERTopic)", step3_topic_modeling)
    if not success:
        logger.error("Pipeline stopped due to topic modeling failure")
        return
    
    # ==================== STEP 4: THEME MAPPING ====================
    
    def step4_theme_mapping():
        from src.theme_mapper import ThemeMapper
        from bertopic import BERTopic
        
        topic_model = BERTopic.load(BERTOPIC_MODEL_PATH)
        
        mapper = ThemeMapper(BABCOCK_THEMES)
        mapping = mapper.create_theme_mapping(topic_model)
        mapper.identify_cross_theme_topics(threshold=0.6)
        mapper.save_mapping(TOPIC_MAPPING_PATH)
        
        return mapper
    
    mapper, success = run_step("4. THEME MAPPING", step4_theme_mapping)
    if not success:
        logger.error("Pipeline stopped due to theme mapping failure")
        return
    
    # ==================== STEP 5: TREND ANALYSIS ====================
    
    def step5_trend_analysis():
        import pandas as pd
        import json
        from src.trend_analyzer import TrendAnalyzer
        
        papers_df = pd.read_csv(PROCESSED_PAPERS_CSV)
        
        with open(TOPIC_MAPPING_PATH, 'r') as f:
            mapping = json.load(f)
        
        trend_analyzer = TrendAnalyzer(mapping, BABCOCK_THEMES)
        
        theme_trends = trend_analyzer.analyze_theme_trends(papers_df)
        emerging_topics = trend_analyzer.identify_emerging_topics(papers_df, threshold=0.5)
        strategic_priorities = trend_analyzer.calculate_strategic_priority(theme_trends)
        
        # Save
        results = {
            'theme_trends': theme_trends,
            'emerging_topics': emerging_topics,
            'strategic_priorities': strategic_priorities
        }
        
        with open(TREND_ANALYSIS_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
    
    results, success = run_step("5. TREND ANALYSIS", step5_trend_analysis)
    if not success:
        logger.error("Pipeline stopped due to trend analysis failure")
        return
    
    # ==================== COMPLETION ====================
    
    total_time = (datetime.now() - overall_start).total_seconds()
    
    print_banner("ANALYSIS COMPLETE!")
    
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Total processing time: {total_time/60:.1f} minutes")
    logger.info(f"Papers analyzed: {len(metadata)}")
    if 'topic_id' in metadata.columns:
        logger.info(f"Topics discovered: {len(set(metadata['topic_id'])) - 1}")
    else:
        logger.info("Topics discovered: Processing...")
    logger.info(f"Themes covered: {len(BABCOCK_THEMES)}")
    
    logger.info(f"\n{'='*80}")
    logger.info("OUTPUT FILES")
    logger.info("="*80)
    logger.info(f"[OK] Raw papers: {RAW_PAPERS_CSV}")
    logger.info(f"[OK] Processed papers: {PROCESSED_PAPERS_CSV}")
    logger.info(f"[OK] BERTopic model: {BERTOPIC_MODEL_PATH}")
    logger.info(f"[OK] Topic-theme mapping: {TOPIC_MAPPING_PATH}")
    logger.info(f"[OK] Trend analysis: {TREND_ANALYSIS_PATH}")
    logger.info(f"[OK] Log file: {log_file}")
    
    logger.info(f"\n{'='*80}")
    logger.info("NEXT STEPS")
    logger.info("="*80)
    logger.info("1. View results: python view_results.py")
    logger.info("2. Launch dashboard: streamlit run dashboard/app.py")
    logger.info("3. Generate reports: python scripts/generate_report.py")
    
    print_banner("SUCCESS! [OK]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)