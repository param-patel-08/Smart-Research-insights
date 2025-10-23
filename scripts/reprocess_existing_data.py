"""
Reprocess existing collected papers with hierarchical theme mapping.

This script runs Steps 2-5 of the analysis pipeline using existing raw data:
- Step 2: Preprocessing (clean abstracts, prepare documents)
- Step 3: Topic Modeling (BERTopic with embeddings)
- Step 4: Theme Mapping (with hierarchical sub-themes)
- Step 5: Trend Analysis (growth rates, emerging topics)

Does NOT re-collect papers - uses existing data/raw/papers_raw.csv
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"reprocess_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_step(step_name: str, step_func):
    """Execute a pipeline step with error handling."""
    try:
        logger.info("=" * 80)
        logger.info(f"STARTING: {step_name}")
        logger.info("=" * 80)
        result = step_func()
        logger.info(f"[SUCCESS] {step_name} completed successfully")
        return result, True
    except Exception as e:
        logger.error(f"[FAILED] {step_name} failed: {str(e)}", exc_info=True)
        return None, False


def main():
    from config.settings import (
        RAW_PAPERS_CSV,
        PROCESSED_PAPERS_CSV,
        BERTOPIC_MODEL_PATH,
        TOPIC_MAPPING_PATH,
        TREND_ANALYSIS_PATH
    )
    from config.themes import BABCOCK_THEMES, BABCOCK_THEMES_HIERARCHICAL
    
    logger.info("=" * 80)
    logger.info("  REPROCESSING EXISTING DATA WITH HIERARCHICAL THEMES")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now()}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Using existing papers from: {RAW_PAPERS_CSV}")
    logger.info("")
    
    # Check if raw data exists
    if not Path(RAW_PAPERS_CSV).exists():
        logger.error(f"Raw data not found at {RAW_PAPERS_CSV}")
        logger.error("Please run full collection first")
        return
    
    # ==================== STEP 2: PREPROCESSING ====================
    
    def step2_preprocessing():
        from src.paper_preprocessor import PaperPreprocessor
        from config.settings import MIN_ABSTRACT_LENGTH, METADATA_CSV
        import pandas as pd
        
        logger.info("Loading existing papers...")
        df = pd.read_csv(RAW_PAPERS_CSV)
        logger.info(f"Loaded {len(df)} papers")
        logger.info(f"Theme distribution: {df['theme'].value_counts().to_dict()}")
        
        preprocessor = PaperPreprocessor(min_abstract_length=MIN_ABSTRACT_LENGTH)
        df = preprocessor.preprocess_abstracts(df)
        
        # Prepare documents and metadata for BERTopic
        documents = df['processed_text'].tolist()
        metadata = df[['title', 'university', 'date', 'authors', 'journal', 'citations', 'theme']].copy()
        
        # Save documents
        documents_file = METADATA_CSV.replace('metadata.csv', 'documents.txt')
        with open(documents_file, 'w', encoding='utf-8') as f:
            for doc in documents:
                f.write(f"{doc}\n")
        
        # Save metadata
        metadata.to_csv(METADATA_CSV, index=False)
        logger.info(f"Preprocessed {len(documents)} documents")
        logger.info(f"Metadata saved to: {METADATA_CSV}")
        
        return documents, metadata
    
    result, success = run_step("2. PREPROCESSING", step2_preprocessing)
    if not success:
        logger.error("Pipeline stopped due to preprocessing failure")
        return
    
    documents, metadata = result
    
    # ==================== STEP 3: TOPIC MODELING ====================
    
    def step3_topic_modeling():
        from src.topic_analyzer import BabcockTopicAnalyzer
        from config.settings import (
            NR_TIME_BINS, EMBEDDINGS_PATH, METADATA_CSV, 
            TOPICS_OVER_TIME_CSV, TOPIC_MODEL_PARAMS
        )
        import pandas as pd
        
        # Load documents
        documents_file = METADATA_CSV.replace('metadata.csv', 'documents.txt')
        with open(documents_file, 'r', encoding='utf-8') as f:
            documents = [line.strip() for line in f if line.strip()]
        
        metadata = pd.read_csv(METADATA_CSV)
        timestamps = pd.to_datetime(metadata['date']).tolist()
        
        # Train model
        logger.info(f"Training BERTopic model with {len(documents)} documents...")
        min_topic_size = TOPIC_MODEL_PARAMS.get('min_topic_size', 15)
        analyzer = BabcockTopicAnalyzer(min_topic_size=min_topic_size, nr_topics=60)
        topics, probs = analyzer.fit_transform(documents, embeddings_path=EMBEDDINGS_PATH)
        
        # Temporal analysis
        logger.info("Analyzing topics over time...")
        topics_over_time = analyzer.get_topics_over_time(
            documents, timestamps, topics, nr_bins=NR_TIME_BINS
        )
        
        # Save
        analyzer.save_model(BERTOPIC_MODEL_PATH)
        logger.info(f"BERTopic model saved to: {BERTOPIC_MODEL_PATH}")
        
        metadata['topic_id'] = topics
        metadata['topic_probability'] = [p.max() if len(p) > 0 else 0 for p in probs]
        metadata.to_csv(PROCESSED_PAPERS_CSV, index=False)
        
        topics_over_time.to_csv(TOPICS_OVER_TIME_CSV, index=False)
        
        return analyzer
    
    analyzer, success = run_step("3. TOPIC MODELING", step3_topic_modeling)
    if not success:
        logger.error("Pipeline stopped due to topic modeling failure")
        return
    
    # ==================== STEP 4: HIERARCHICAL THEME MAPPING ====================
    
    def step4_hierarchical_theme_mapping():
        from src.theme_mapper import ThemeMapper
        from bertopic import BERTopic
        
        topic_model = BERTopic.load(BERTOPIC_MODEL_PATH)
        
        mapper = ThemeMapper(BABCOCK_THEMES)
        # Use hierarchical themes for sub-theme detection
        logger.info("Creating hierarchical theme mapping (40 sub-themes)...")
        mapping = mapper.create_theme_mapping(
            topic_model, 
            hierarchical_themes=BABCOCK_THEMES_HIERARCHICAL
        )
        
        # Identify cross-theme topics
        cross_theme = mapper.identify_cross_theme_topics(threshold=0.6)
        if cross_theme:
            logger.info(f"Found {len(cross_theme)} cross-theme topics")
        
        mapper.save_mapping(TOPIC_MAPPING_PATH)
        logger.info(f"Hierarchical mapping saved to: {TOPIC_MAPPING_PATH}")
        
        return mapper
    
    mapper, success = run_step("4. HIERARCHICAL THEME MAPPING", step4_hierarchical_theme_mapping)
    if not success:
        logger.error("Pipeline stopped due to theme mapping failure")
        return
    
    # ==================== STEP 5: TREND ANALYSIS ====================
    
    def step5_trend_analysis():
        from src.trend_analyzer import TrendAnalyzer
        import pandas as pd
        import json
        
        papers_df = pd.read_csv(PROCESSED_PAPERS_CSV)
        
        # Load the hierarchical mapping we just created
        with open(TOPIC_MAPPING_PATH, 'r') as f:
            mapping = json.load(f)
        
        logger.info("Analyzing trends with hierarchical themes...")
        trend_analyzer = TrendAnalyzer(mapping, BABCOCK_THEMES)
        
        theme_trends = trend_analyzer.analyze_theme_trends(papers_df)
        emerging_topics = trend_analyzer.identify_emerging_topics(papers_df, threshold=0.5)
        strategic_priorities = trend_analyzer.calculate_strategic_priority(theme_trends)
        
        # Save results
        results = {
            'theme_trends': theme_trends,
            'emerging_topics': emerging_topics,
            'strategic_priorities': strategic_priorities
        }
        
        with open(TREND_ANALYSIS_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Trend analysis saved to: {TREND_ANALYSIS_PATH}")
        
        return results
    
    results, success = run_step("5. TREND ANALYSIS", step5_trend_analysis)
    if not success:
        logger.error("Pipeline stopped due to trend analysis failure")
        return
    
    # ==================== COMPLETION SUMMARY ====================
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("  REPROCESSING COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Completed at: {datetime.now()}")
    logger.info("")
    logger.info("Updated files:")
    logger.info(f"  [DONE] {PROCESSED_PAPERS_CSV}")
    logger.info(f"  [DONE] {BERTOPIC_MODEL_PATH}")
    logger.info(f"  [DONE] {TOPIC_MAPPING_PATH} (with sub-themes)")
    logger.info(f"  [DONE] {TREND_ANALYSIS_PATH}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Run: python launch_dashboard.py")
    logger.info("  2. View hierarchical themes in dashboard")
    logger.info("  3. Analyze emerging topics at sub-theme level")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nReprocessing interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Reprocessing failed: {str(e)}", exc_info=True)
        sys.exit(1)
