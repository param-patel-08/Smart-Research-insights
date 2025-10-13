"""
Run Steps 3-5 only (Topic Modeling, Theme Mapping, Trend Analysis)
Use this when Steps 1-2 (Collection & Preprocessing) are already complete
"""

import logging
import time
import pandas as pd
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import settings
from config.settings import (
    PROCESSED_PAPERS_CSV,
    METADATA_CSV,
    EMBEDDINGS_PATH,
    BERTOPIC_MODEL_PATH,
    TOPICS_OVER_TIME_CSV,
    TOPIC_MAPPING_PATH,
    TREND_ANALYSIS_PATH,
    NR_TIME_BINS,
    TOPIC_MODEL_PARAMS
)

def run_step(name, function, *args, **kwargs):
    """Run a pipeline step with timing and error handling"""
    logger.info(f"\n{'='*80}")
    logger.info(f"  STARTING: {name}")
    logger.info(f"{'='*80}\n")
    
    start_time = time.time()
    try:
        result = function(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"[OK] {name} completed in {elapsed:.1f} seconds")
        return result, True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[ERROR] {name} failed after {elapsed:.1f} seconds: {e}")
        import traceback
        traceback.print_exc()
        return None, False


def step3_topic_modeling():
    """Step 3: Topic Modeling with BERTopic"""
    from src.topic_analyzer import BabcockTopicAnalyzer
    
    # Load documents
    documents_file = METADATA_CSV.replace('metadata.csv', 'documents.txt')
    with open(documents_file, 'r', encoding='utf-8') as f:
        documents = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Loaded {len(documents)} documents")
    
    metadata = pd.read_csv(METADATA_CSV)
    timestamps = pd.to_datetime(metadata['date']).tolist()
    
    # Train model (use config params for smaller datasets)
    logger.info(f"Training BERTopic with min_topic_size={TOPIC_MODEL_PARAMS['min_topic_size']}")
    analyzer = BabcockTopicAnalyzer(
        min_topic_size=TOPIC_MODEL_PARAMS['min_topic_size'],
        nr_topics=30  # Reduced from 60 for smaller dataset
    )
    topics, probs = analyzer.fit_transform(documents, embeddings_path=EMBEDDINGS_PATH)
    
    logger.info(f"Found {len(set(topics))} topics")
    
    # Temporal analysis
    topics_over_time = analyzer.get_topics_over_time(
        documents, timestamps, topics, nr_bins=NR_TIME_BINS
    )
    
    # Save
    analyzer.save_model(BERTOPIC_MODEL_PATH)
    logger.info(f"Saved model to {BERTOPIC_MODEL_PATH}")
    
    metadata['topic_id'] = topics
    metadata['topic_probability'] = [p.max() if len(p) > 0 else 0 for p in probs]
    metadata.to_csv(PROCESSED_PAPERS_CSV, index=False)
    logger.info(f"Saved processed papers to {PROCESSED_PAPERS_CSV}")
    
    topics_over_time.to_csv(TOPICS_OVER_TIME_CSV, index=False)
    logger.info(f"Saved topics over time to {TOPICS_OVER_TIME_CSV}")
    
    return analyzer


def step4_theme_mapping():
    """Step 4: Map BERTopic topics to Babcock themes"""
    from src.theme_mapper import ThemeMapper
    from config.themes import BABCOCK_THEMES
    from bertopic import BERTopic
    
    # Load BERTopic model
    topic_model = BERTopic.load(BERTOPIC_MODEL_PATH)
    
    # Create theme mapping
    mapper = ThemeMapper(babcock_themes=BABCOCK_THEMES)
    mapping = mapper.create_theme_mapping(topic_model)
    mapper.identify_cross_theme_topics(threshold=0.6)
    mapper.save_mapping(TOPIC_MAPPING_PATH)
    
    logger.info(f"Mapped {len(mapping)} topics to themes")
    return mapping


def step5_trend_analysis():
    """Step 5: Analyze trends and generate insights"""
    from src.trend_analyzer import TrendAnalyzer
    from config.themes import BABCOCK_THEMES
    import json
    import pandas as pd
    
    # Load data
    papers_df = pd.read_csv(PROCESSED_PAPERS_CSV)
    
    with open(TOPIC_MAPPING_PATH, 'r') as f:
        topic_mapping = json.load(f)
    
    # Create analyzer
    analyzer = TrendAnalyzer(
        topic_theme_mapping=topic_mapping,
        babcock_themes=BABCOCK_THEMES
    )
    
    # Analyze trends
    theme_trends = analyzer.analyze_theme_trends(papers_df)
    emerging_topics = analyzer.identify_emerging_topics(papers_df, threshold=0.5)
    strategic_priorities = analyzer.calculate_strategic_priority(theme_trends)
    
    # Save results
    results = {
        'theme_trends': theme_trends,
        'emerging_topics': emerging_topics,
        'strategic_priorities': strategic_priorities
    }
    
    with open(TREND_ANALYSIS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Generated trend analysis with {len(theme_trends)} theme trends")
    logger.info(f"Saved analysis to {TREND_ANALYSIS_PATH}")
    return results


if __name__ == "__main__":
    print("\n" + "="*80)
    print("  RESEARCH TREND ANALYZER - STEPS 3-5 ONLY")
    print("="*80 + "\n")
    
    # Check prerequisites
    if not Path(PROCESSED_PAPERS_CSV).exists():
        logger.error(f"Missing {PROCESSED_PAPERS_CSV}")
        logger.error("Please run Steps 1-2 first (data collection & preprocessing)")
        exit(1)
    
    if not Path(METADATA_CSV).exists():
        logger.error(f"Missing {METADATA_CSV}")
        logger.error("Please run Steps 1-2 first (data collection & preprocessing)")
        exit(1)
    
    # Run Steps 3-5
    analyzer, success = run_step("STEP 3: TOPIC MODELING", step3_topic_modeling)
    if not success:
        logger.error("Pipeline stopped due to topic modeling failure")
        exit(1)
    
    mapping, success = run_step("STEP 4: THEME MAPPING", step4_theme_mapping)
    if not success:
        logger.error("Pipeline stopped due to theme mapping failure")
        exit(1)
    
    trends, success = run_step("STEP 5: TREND ANALYSIS", step5_trend_analysis)
    if not success:
        logger.error("Pipeline stopped due to trend analysis failure")
        exit(1)
    
    print("\n" + "="*80)
    print("  ALL STEPS COMPLETED SUCCESSFULLY!")
    print("="*80)
    print(f"\nResults saved to:")
    print(f"  - {PROCESSED_PAPERS_CSV}")
    print(f"  - {BERTOPIC_MODEL_PATH}")
    print(f"  - {TOPIC_MAPPING_PATH}")
    print(f"  - {TREND_ANALYSIS_PATH}")
    print(f"\nYou can now launch the dashboard:")
    print(f"  python launch_dashboard.py")
    print()
