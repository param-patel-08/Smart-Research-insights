"""
BERTopic Topic Analyzer
Discovers research topics from papers using BERTopic
"""

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import pandas as pd
import pickle
from typing import List, Tuple
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TopicAnalyzer:
    """
    BERTopic analysis optimized for academic papers
    """
    
    def __init__(self, min_topic_size: int = 15, nr_topics: int = 60):
        """
        Initialize analyzer
        
        Args:
            min_topic_size: Minimum papers per topic
            nr_topics: Target number of topics (auto if None)
        """
        self.min_topic_size = min_topic_size
        self.nr_topics = nr_topics
        self.topic_model = None
        logger.info(f"Topic Analyzer initialized")
        logger.info(f"  Min topic size: {min_topic_size}")
        logger.info(f"  Target topics: {nr_topics}")
    
    def create_bertopic_model(self):
        """
        Initialize BERTopic with optimized parameters for academic papers
        """
        logger.info("\nInitializing BERTopic model...")
        
        # Embedding model - fast and effective for academic text
        logger.info("  Loading embedding model: all-MiniLM-L6-v2")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # UMAP for dimensionality reduction
        umap_model = UMAP(
            n_neighbors=15,
            n_components=5,
            min_dist=0.0,
            metric='cosine',
            random_state=42
        )
        
        # HDBSCAN for clustering
        hdbscan_model = HDBSCAN(
            min_cluster_size=self.min_topic_size,
            min_samples=5,
            cluster_selection_method='eom',
            prediction_data=True
        )
        
        # CountVectorizer for topic representation
        vectorizer_model = CountVectorizer(
            ngram_range=(1, 3),
            stop_words='english',
            min_df=2,
            max_df=0.95
        )
        
        # Create BERTopic model
        self.topic_model = BERTopic(
            embedding_model=embedding_model,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            min_topic_size=self.min_topic_size,
            nr_topics=self.nr_topics,
            calculate_probabilities=True,
            verbose=True
        )
        
        logger.info("[OK] BERTopic model initialized")
        
        return self.topic_model
    
    def fit_transform(self, documents: List[str], embeddings_path: str = None) -> Tuple:
        """
        Train BERTopic model on documents
        
        Args:
            documents: List of paper texts
            embeddings_path: Optional path to save/load embeddings
            
        Returns:
            (topics, probabilities)
        """
        if self.topic_model is None:
            self.create_bertopic_model()
        
        # Check if embeddings already exist and match current documents
        embeddings = None
        if embeddings_path and os.path.exists(embeddings_path):
            try:
                logger.info(f"\n[OK] Loading cached embeddings from {embeddings_path}")
                cached = np.load(embeddings_path)
                if isinstance(cached, np.ndarray) and cached.ndim == 2 and cached.shape[0] == len(documents):
                    embeddings = cached
                    logger.info(f"[OK] Using cached embeddings with shape {cached.shape}")
                else:
                    logger.warning(
                        f"[WARN] Ignoring stale embeddings cache. Expected ({len(documents)}, vector_dim) "
                        f"but got {getattr(cached, 'shape', None)}"
                    )
            except Exception as e:
                logger.warning(f"[WARN] Failed to load embeddings cache ({e}); will recompute.")
        if embeddings is None:
            logger.info("\nGenerating embeddings (this may take 1-2 minutes)...")
        
        # Fit model
        logger.info(f"\nTraining BERTopic on {len(documents)} documents...")
        logger.info("This will take approximately 60-90 seconds...")
        
        start_time = datetime.now()
        topics, probs = self.topic_model.fit_transform(documents, embeddings)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Save embeddings for future use (save only when we generated fresh)
        if embeddings_path and (not os.path.exists(embeddings_path) or embeddings is None):
            try:
                # SentenceTransformer provides .encode
                emb_model = self.topic_model.embedding_model
                if hasattr(emb_model, 'encode'):
                    fresh_emb = emb_model.encode(documents, show_progress_bar=False, normalize_embeddings=False)
                else:
                    # Fallback to call that some wrappers expose
                    fresh_emb = emb_model.embed_documents(documents)
                np.save(embeddings_path, fresh_emb)
                logger.info(f"[OK] Saved embeddings to {embeddings_path} with shape {np.array(fresh_emb).shape}")
            except Exception as e:
                logger.warning(f"[WARN] Could not save embeddings cache: {e}")
        
        # Log results
        unique_topics = len(set(topics)) - 1  # Exclude -1 (outliers)
        outliers = sum(1 for t in topics if t == -1)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"BERTOPIC TRAINING COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Processing time: {elapsed:.1f} seconds")
        logger.info(f"Topics discovered: {unique_topics}")
        logger.info(f"Outliers: {outliers} ({outliers/len(topics)*100:.1f}%)")
        logger.info(f"Papers per topic (avg): {len(documents)/unique_topics:.1f}")
        
        return topics, probs
    
    def get_topics_over_time(self, 
                            documents: List[str],
                            timestamps: List[datetime],
                            topics: List[int],
                            nr_bins: int = 8) -> pd.DataFrame:
        """
        Analyze topic evolution over time
        
        Args:
            documents: List of paper texts
            timestamps: Publication dates
            topics: Topic assignments from fit_transform
            nr_bins: Number of time periods (8 = quarterly for 2 years)
            
        Returns:
            DataFrame with topic counts per time period
        """
        logger.info("\nAnalyzing topics over time...")
        logger.info(f"  Time bins: {nr_bins} (quarterly analysis)")
        
        topics_over_time = self.topic_model.topics_over_time(
            docs=documents,
            timestamps=timestamps,
            topics=topics,
            nr_bins=nr_bins
        )
        
        logger.info(f"[OK] Temporal analysis complete")
        logger.info(f"  Time periods analyzed: {topics_over_time['Timestamp'].nunique()}")
        
        return topics_over_time
    
    def get_topic_info(self) -> pd.DataFrame:
        """
        Get detailed information about each topic
        """
        return self.topic_model.get_topic_info()
    
    def get_representative_docs(self, topic_id: int, n_docs: int = 5) -> List[str]:
        """
        Get most representative documents for a topic
        """
        return self.topic_model.get_representative_docs(topic_id)[:n_docs]
    
    def save_model(self, filepath: str) -> None:
        """
        Save trained model to disk
        """
        self.topic_model.save(filepath, serialization="pickle")
        logger.info(f"\n[OK] Model saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """
        Load trained model from disk
        """
        self.topic_model = BERTopic.load(filepath)
        logger.info(f"[OK] Model loaded from {filepath}")
    
    def get_topic_keywords(self, topic_id: int, n_words: int = 10) -> List[str]:
        """
        Get keywords for a specific topic
        
        Args:
            topic_id: Topic ID
            n_words: Number of keywords to return
            
        Returns:
            List of keywords
        """
        topic_words = self.topic_model.get_topic(topic_id)
        return [word for word, score in topic_words[:n_words]]


# ==================== USAGE EXAMPLE ====================

def main():
    """
    Example usage of TopicAnalyzer
    """
    from config.settings import (
        EMBEDDINGS_PATH,
        BERTOPIC_MODEL_PATH,
        PROCESSED_PAPERS_CSV,
        TOPICS_OVER_TIME_CSV,
        METADATA_CSV,
        NR_TIME_BINS
    )
    
    logger.info("="*80)
    logger.info("BERTOPIC TOPIC ANALYSIS")
    logger.info("="*80)
    
    # Load documents
    logger.info(f"\nLoading documents...")
    
    documents_file = METADATA_CSV.replace('metadata.csv', 'documents.txt')
    with open(documents_file, 'r', encoding='utf-8') as f:
        documents = [line.strip() for line in f if line.strip()]
    
    logger.info(f"[OK] Loaded {len(documents)} documents")
    
    # Load metadata for timestamps
    metadata = pd.read_csv(METADATA_CSV)
    timestamps = pd.to_datetime(metadata['date']).tolist()
    
    # Initialize analyzer
    analyzer = TopicAnalyzer(min_topic_size=15, nr_topics=60)
    
    # Train model
    topics, probs = analyzer.fit_transform(
        documents, 
        embeddings_path=EMBEDDINGS_PATH
    )
    
    # Temporal analysis
    topics_over_time = analyzer.get_topics_over_time(
        documents, 
        timestamps, 
        topics,
        nr_bins=NR_TIME_BINS
    )
    
    # Save results
    logger.info("\nSaving results...")
    
    # Save model
    analyzer.save_model(BERTOPIC_MODEL_PATH)
    
    # Save topic assignments
    metadata['topic_id'] = topics
    metadata['topic_probability'] = [p.max() if len(p) > 0 else 0 for p in probs]
    metadata.to_csv(PROCESSED_PAPERS_CSV, index=False)
    logger.info(f"[OK] Saved papers with topics to {PROCESSED_PAPERS_CSV}")
    
    # Save temporal data
    topics_over_time.to_csv(TOPICS_OVER_TIME_CSV, index=False)
    logger.info(f"[OK] Saved temporal analysis to {TOPICS_OVER_TIME_CSV}")
    
    # Show topic summary
    topic_info = analyzer.get_topic_info()
    
    logger.info("\n" + "="*80)
    logger.info("TOP 10 TOPICS BY SIZE")
    logger.info("="*80)
    
    for idx, row in topic_info.head(10).iterrows():
        if row['Topic'] == -1:
            continue
        topic_id = row['Topic']
        count = row['Count']
        keywords = analyzer.get_topic_keywords(topic_id, n_words=5)
        logger.info(f"Topic {topic_id}: {', '.join(keywords)} ({count} papers)")
    
    logger.info("\n[OK] Topic analysis complete!")


if __name__ == "__main__":
    main()