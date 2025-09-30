"""
Theme Mapper for Babcock Research Trends
Maps BERTopic topics to Babcock's 9 strategic themes
"""

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pandas as pd
import json
from typing import Dict, Tuple, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThemeMapper:
    """
    Map BERTopic topics to Babcock's 9 strategic themes
    """
    
    def __init__(self, babcock_themes: Dict):
        """
        Initialize mapper
        
        Args:
            babcock_themes: Dictionary of Babcock strategic themes
        """
        self.babcock_themes = babcock_themes
        self.topic_theme_mapping = {}
        logger.info(f"Theme Mapper initialized with {len(babcock_themes)} themes")
    
    def calculate_keyword_similarity(self, 
                                     topic_keywords: List[Tuple[str, float]],
                                     theme_keywords: List[str]) -> float:
        """
        Calculate similarity between topic keywords and theme keywords
        using TF-IDF and cosine similarity
        
        Args:
            topic_keywords: List of (word, score) tuples from BERTopic
            theme_keywords: List of theme keywords
            
        Returns:
            Similarity score (0-1)
        """
        # Extract just the words from topic keywords
        topic_words = [word for word, score in topic_keywords[:20]]
        
        # Create documents
        topic_doc = ' '.join(topic_words)
        theme_doc = ' '.join(theme_keywords)
        
        # Calculate TF-IDF
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([topic_doc, theme_doc])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            # Handle edge cases
            similarity = 0.0
        
        # Also check for direct keyword overlaps (boost score)
        overlap_count = len(set(topic_words) & set([k.lower() for k in theme_keywords]))
        overlap_bonus = overlap_count * 0.1
        
        final_score = min(1.0, similarity + overlap_bonus)
        
        return final_score
    
    def map_topic_to_theme(self, 
                          topic_id: int, 
                          topic_keywords: List[Tuple[str, float]]) -> Tuple[str, float, Dict]:
        """
        Map a single topic to the best matching Babcock theme
        
        Args:
            topic_id: BERTopic topic ID
            topic_keywords: Keywords from BERTopic
            
        Returns:
            (theme_name, confidence_score, all_scores)
        """
        scores = {}
        
        for theme_name, theme_data in self.babcock_themes.items():
            similarity = self.calculate_keyword_similarity(
                topic_keywords,
                theme_data['keywords']
            )
            
            # Weight by strategic priority
            if theme_data['strategic_priority'] == 'HIGH':
                similarity *= 1.1  # Slight boost for high priority themes
            
            scores[theme_name] = similarity
        
        # Get best match
        best_theme = max(scores, key=scores.get)
        confidence = scores[best_theme]
        
        return best_theme, confidence, scores
    
    def create_theme_mapping(self, topic_model) -> Dict:
        """
        Create complete mapping of all topics to themes
        
        Args:
            topic_model: Trained BERTopic model
            
        Returns:
            Dictionary: {topic_id: {'theme': str, 'confidence': float, 'keywords': list}}
        """
        logger.info("\n" + "="*80)
        logger.info("MAPPING TOPICS TO BABCOCK THEMES")
        logger.info("="*80)
        
        topic_info = topic_model.get_topic_info()
        
        for idx, row in topic_info.iterrows():
            topic_id = row['Topic']
            
            # Skip outlier topic
            if topic_id == -1:
                continue
            
            # Get topic keywords
            topic_keywords = topic_model.get_topic(topic_id)
            
            # Map to theme
            theme, confidence, all_scores = self.map_topic_to_theme(topic_id, topic_keywords)
            
            self.topic_theme_mapping[str(topic_id)] = {
                'theme': theme,
                'confidence': confidence,
                'all_scores': all_scores,
                'keywords': [word for word, score in topic_keywords[:10]],
                'count': int(row['Count'])
            }
            
            logger.debug(f"Topic {topic_id} -> {theme} (confidence: {confidence:.3f})")
        
        # Log summary statistics
        self._log_mapping_summary()
        
        return self.topic_theme_mapping
    
    def _log_mapping_summary(self):
        """Log summary statistics of the mapping"""
        confidences = [data['confidence'] for data in self.topic_theme_mapping.values()]
        
        logger.info(f"\n✓ Mapped {len(self.topic_theme_mapping)} topics to themes")
        logger.info(f"  Average confidence: {np.mean(confidences):.3f}")
        logger.info(f"  Confidence range: {np.min(confidences):.3f} - {np.max(confidences):.3f}")
        
        # Count topics per theme
        theme_counts = {}
        for data in self.topic_theme_mapping.values():
            theme = data['theme']
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        logger.info("\n  Topics per theme:")
        for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"    {theme}: {count} topics")
    
    def identify_cross_theme_topics(self, threshold: float = 0.6) -> List[Dict]:
        """
        Find topics that strongly relate to multiple themes
        
        Args:
            threshold: Minimum score to consider a theme relevant
            
        Returns:
            List of topics with multiple strong theme associations
        """
        cross_theme_topics = []
        
        for topic_id, data in self.topic_theme_mapping.items():
            # Count themes above threshold
            strong_themes = [theme for theme, score in data['all_scores'].items() 
                           if score >= threshold]
            
            if len(strong_themes) > 1:
                cross_theme_topics.append({
                    'topic_id': topic_id,
                    'themes': strong_themes,
                    'scores': {theme: data['all_scores'][theme] for theme in strong_themes},
                    'keywords': data['keywords']
                })
        
        logger.info(f"\n✓ Found {len(cross_theme_topics)} cross-theme topics")
        
        return cross_theme_topics
    
    def save_mapping(self, filepath: str):
        """Save theme mapping to JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.topic_theme_mapping, f, indent=2)
        logger.info(f"✓ Saved theme mapping to {filepath}")
    
    def load_mapping(self, filepath: str):
        """Load theme mapping from JSON"""
        with open(filepath, 'r') as f:
            self.topic_theme_mapping = json.load(f)
        logger.info(f"✓ Loaded theme mapping from {filepath}")


# ==================== USAGE EXAMPLE ====================

def main():
    """
    Example usage of ThemeMapper
    """
    from config.settings import BERTOPIC_MODEL_PATH, TOPIC_MAPPING_PATH
    from config.themes import BABCOCK_THEMES
    from bertopic import BERTopic
    
    logger.info("="*80)
    logger.info("THEME MAPPING")
    logger.info("="*80)
    
    # Load trained model
    logger.info(f"\nLoading BERTopic model from {BERTOPIC_MODEL_PATH}...")
    topic_model = BERTopic.load(BERTOPIC_MODEL_PATH)
    logger.info("✓ Model loaded")
    
    # Create mapper
    mapper = ThemeMapper(BABCOCK_THEMES)
    
    # Create mapping
    mapping = mapper.create_theme_mapping(topic_model)
    
    # Identify cross-theme topics
    cross_theme = mapper.identify_cross_theme_topics(threshold=0.6)
    
    if cross_theme:
        logger.info("\n  Cross-theme topics (relevant to multiple areas):")
        for topic in cross_theme[:5]:  # Show first 5
            logger.info(f"    Topic {topic['topic_id']}: {', '.join(topic['keywords'][:5])}")
            logger.info(f"      Themes: {', '.join(topic['themes'])}")
    
    # Save mapping
    mapper.save_mapping(TOPIC_MAPPING_PATH)
    
    logger.info("\n✓ Theme mapping complete!")


if __name__ == "__main__":
    main()