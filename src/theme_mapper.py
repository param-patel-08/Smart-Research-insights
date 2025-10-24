"""
Theme Mapper
Maps BERTopic topics to the organization's 9 strategic themes.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DEFAULT_THEME_THRESHOLDS: Dict[str, float] = {
    "Defense_Security": 0.005,
}


class ThemeMapper:
    """
    Map BERTopic topics to the organization's strategic themes using keyword similarity.
    """

    def __init__(
        self,
    strategic_themes: Dict[str, Dict],
        min_similarity: float = 0.01,
        theme_thresholds: Optional[Dict[str, float]] = None,
    ):
        """
        Args:
            strategic_themes: Dictionary of themes with keywords and metadata.
            min_similarity: Minimum cosine similarity required to assign a theme.
        """
        self.strategic_themes = strategic_themes
        self.min_similarity = min_similarity
        self.theme_thresholds = {**DEFAULT_THEME_THRESHOLDS, **(theme_thresholds or {})}
        self.topic_theme_mapping: Dict[str, Dict] = {}
        self._vectorizer = TfidfVectorizer()
        logger.info(
            "Theme Mapper initialized with %d themes (default threshold=%.3f)",
            len(strategic_themes),
            min_similarity,
        )
        if self.theme_thresholds:
            logger.info("Theme-specific thresholds: %s", self.theme_thresholds)

    def calculate_keyword_similarity(
        self,
        topic_keywords: List[Tuple[str, float]],
        theme_keywords: List[str],
    ) -> float:
        """
        Calculate cosine similarity between topic keywords and theme keywords.
        """
        topic_words = [str(word).lower() for word, _ in topic_keywords[:20] if isinstance(word, str)]
        theme_words = [str(word).lower() for word in theme_keywords]

        topic_doc = " ".join(topic_words)
        theme_doc = " ".join(theme_words)

        if not topic_doc or not theme_doc:
            return 0.0

        try:
            matrix = self._vectorizer.fit_transform([topic_doc, theme_doc])
            if matrix.shape[1] == 0:
                return 0.0
            return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        except ValueError:
            return 0.0

    def map_topic_to_theme(
        self,
        topic_id: int,
        topic_keywords: List[Tuple[str, float]],
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Determine the best matching theme for a topic.
        """
        scores: Dict[str, float] = {}
        for theme_name, theme_data in self.strategic_themes.items():
            score = self.calculate_keyword_similarity(topic_keywords, theme_data.get("keywords", []))
            scores[theme_name] = score

        best_theme = max(scores, key=scores.get) if scores else "Other"
        best_score = scores.get(best_theme, 0.0)

        threshold = self.theme_thresholds.get(best_theme, self.min_similarity)

        if best_score < threshold:
            return "Other", best_score, scores
        return best_theme, best_score, scores

    def map_topic_to_sub_theme(
        self,
        topic_keywords: List[Tuple[str, float]],
        parent_theme: str,
        hierarchical_themes: Dict,
    ) -> Tuple[str, float]:
        """
        Map a topic to a sub-theme within a parent theme.
        Returns (sub_theme_name, confidence_score)
        """
        if parent_theme not in hierarchical_themes:
            return None, 0.0
        
        sub_themes = hierarchical_themes[parent_theme].get('sub_themes', {})
        if not sub_themes:
            return None, 0.0
        
        scores = {}
        for sub_theme_name, sub_theme_keywords in sub_themes.items():
            score = self.calculate_keyword_similarity(topic_keywords, sub_theme_keywords)
            scores[sub_theme_name] = score
        
        if not scores:
            return None, 0.0
        
        best_sub_theme = max(scores, key=scores.get)
        best_score = scores[best_sub_theme]
        
        return best_sub_theme, float(best_score)

    def create_theme_mapping(self, topic_model, hierarchical_themes: Optional[Dict] = None) -> Dict[str, Dict]:
        """
        Build mapping from BERTopic model to strategic themes.
        
        Args:
            topic_model: BERTopic model
            hierarchical_themes: Optional dict of hierarchical themes with sub-themes
                                If provided, will also map topics to sub-themes
        """
        logger.info("=" * 80)
        logger.info("MAPPING TOPICS TO STRATEGIC THEMES")
        if hierarchical_themes:
            logger.info("Using HIERARCHICAL mapping (parent + sub-themes)")
        logger.info("=" * 80)

        topic_info = topic_model.get_topic_info()
        mapping: Dict[str, Dict] = {}

        for _, row in topic_info.iterrows():
            topic_id = row["Topic"]
            if topic_id == -1:
                continue  # Skip outlier cluster

            keywords = topic_model.get_topic(topic_id)
            theme, confidence, all_scores = self.map_topic_to_theme(topic_id, keywords)

            topic_data = {
                "theme": theme,
                "confidence": float(confidence),
                "all_scores": {k: float(v) for k, v in all_scores.items()},
                "keywords": [word for word, _ in keywords[:10]],
                "count": int(row.get("Count", 0)),
            }
            
            # Add sub-theme mapping if hierarchical themes provided
            if hierarchical_themes and theme != "Other":
                sub_theme, sub_confidence = self.map_topic_to_sub_theme(
                    keywords, theme, hierarchical_themes
                )
                if sub_theme:
                    topic_data["sub_theme"] = sub_theme
                    topic_data["sub_theme_confidence"] = float(sub_confidence)
                    logger.debug("Topic %s -> %s > %s (sub-conf %.3f)", 
                               topic_id, theme, sub_theme, sub_confidence)
                else:
                    topic_data["sub_theme"] = None
                    topic_data["sub_theme_confidence"] = 0.0
            else:
                topic_data["sub_theme"] = None
                topic_data["sub_theme_confidence"] = 0.0

            mapping[str(topic_id)] = topic_data
            logger.debug("Topic %s -> %s (confidence %.3f)", topic_id, theme, confidence)

        self.topic_theme_mapping = mapping
        self._log_mapping_summary(hierarchical_themes is not None)
        return mapping

    def _log_mapping_summary(self, is_hierarchical: bool = False) -> None:
        """Log summary statistics of the mapping.
        
        Args:
            is_hierarchical: Whether hierarchical mapping was used
        """
        if not self.topic_theme_mapping:
            logger.warning("No topics were mapped to themes.")
            return

        confidences = [data["confidence"] for data in self.topic_theme_mapping.values()]
        theme_counts: Dict[str, int] = {}
        for data in self.topic_theme_mapping.values():
            theme = data["theme"]
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

        logger.info("Mapped %d topics", len(self.topic_theme_mapping))
        if confidences:
            logger.info("Average confidence: %.3f", float(np.mean(confidences)))
            logger.info(
                "Confidence range: %.3f - %.3f",
                float(np.min(confidences)),
                float(np.max(confidences)),
            )
        logger.info("Topics per theme: %s", theme_counts)
        
        # TEMPORARY: Log sub-theme distribution if hierarchical mapping was used
        if is_hierarchical:
            sub_theme_counts = {}
            sub_confidences = []
            for data in self.topic_theme_mapping.values():
                sub_theme = data.get("sub_theme")
                if sub_theme:
                    sub_theme_counts[sub_theme] = sub_theme_counts.get(sub_theme, 0) + 1
                    sub_confidences.append(data.get("sub_theme_confidence", 0))
            
            if sub_theme_counts:
                avg_sub_confidence = float(np.mean(sub_confidences)) if sub_confidences else 0.0
                top_sub_themes = dict(sorted(sub_theme_counts.items(), key=lambda x: x[1], reverse=True)[:10])
                logger.info("Sub-themes detected: %d unique sub-themes", len(sub_theme_counts))
                logger.info("Average sub-theme confidence: %.3f", avg_sub_confidence)
                logger.info("Topics per sub-theme (top 10): %s", top_sub_themes)

    def identify_cross_theme_topics(self, threshold: float = 0.6) -> List[Dict]:
        """
        Find topics that strongly relate to multiple themes.
        """
        cross_theme_topics = []
        for topic_id, data in self.topic_theme_mapping.items():
            strong_themes = [theme for theme, score in data["all_scores"].items() if score >= threshold]
            if len(strong_themes) > 1:
                cross_theme_topics.append(
                    {
                        "topic_id": topic_id,
                        "themes": strong_themes,
                        "scores": {theme: data["all_scores"][theme] for theme in strong_themes},
                        "keywords": data["keywords"],
                    }
                )
        logger.info("Found %d cross-theme topics with threshold %.2f", len(cross_theme_topics), threshold)
        return cross_theme_topics

    def save_mapping(self, filepath: str) -> None:
        """Persist mapping to JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.topic_theme_mapping, f, indent=2)
        logger.info("Saved theme mapping to %s", filepath)

    def load_mapping(self, filepath: str) -> None:
        """Load mapping from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            self.topic_theme_mapping = json.load(f)
        logger.info("Loaded theme mapping from %s", filepath)


def main():
    """Manual test helper for the theme mapper."""
    from bertopic import BERTopic

    from config.settings import BERTOPIC_MODEL_PATH, TOPIC_MAPPING_PATH
    from config.themes import STRATEGIC_THEMES

    logger.info("=" * 80)
    logger.info("THEME MAPPING")
    logger.info("=" * 80)

    topic_model = BERTopic.load(BERTOPIC_MODEL_PATH)
    mapper = ThemeMapper(STRATEGIC_THEMES)

    mapper.create_theme_mapping(topic_model)
    mapper.identify_cross_theme_topics(threshold=0.6)
    mapper.save_mapping(TOPIC_MAPPING_PATH)

    logger.info("Theme mapping complete.")


# TEMPORARY: Test hierarchical theme mapping
def _test_hierarchical_mapping():
    """Test that sub-theme detection works with hierarchical themes"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from bertopic import BERTopic
    from config.themes import STRATEGIC_THEMES, STRATEGIC_THEMES_HIERARCHICAL
    from config.settings import BERTOPIC_MODEL_PATH, TOPIC_MAPPING_PATH
    import json
    
    logger.info("=" * 80)
    logger.info("TESTING HIERARCHICAL THEME MAPPING")
    logger.info("=" * 80)
    
    # Check if model exists
    if not os.path.exists(BERTOPIC_MODEL_PATH):
        logger.error(f"BERTopic model not found at {BERTOPIC_MODEL_PATH}")
        logger.info("Please run the full analysis first to generate the model")
        return
    
    # Load BERTopic model
    logger.info("Loading BERTopic model...")
    topic_model = BERTopic.load(BERTOPIC_MODEL_PATH)
    
    # Create mapper and generate hierarchical mapping
    logger.info("Creating hierarchical theme mapping...")
    mapper = ThemeMapper(STRATEGIC_THEMES)
    mapping = mapper.create_theme_mapping(topic_model, hierarchical_themes=STRATEGIC_THEMES_HIERARCHICAL)
    
    # Display sample mappings
    logger.info("\nSample topic mappings with sub-themes:")
    count = 0
    for topic_id, data in mapping.items():
        if count >= 5:  # Show first 5
            break
        logger.info(f"\nTopic {topic_id}:")
        logger.info(f"  Parent Theme: {data['theme']} (conf: {data['confidence']:.3f})")
        if data.get('sub_theme'):
            logger.info(f"  Sub-Theme: {data['sub_theme']} (conf: {data['sub_theme_confidence']:.3f})")
        logger.info(f"  Keywords: {', '.join(data['keywords'][:5])}")
        count += 1
    
    # Count statistics
    with_subtheme = sum(1 for d in mapping.values() if d.get('sub_theme'))
    logger.info(f"\nTopics with sub-theme assignments: {with_subtheme}/{len(mapping)}")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        _test_hierarchical_mapping()
    else:
        main()
