"""
Theme Mapper for Babcock Research Trends
Maps BERTopic topics to Babcock's 9 strategic themes.
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
    Map BERTopic topics to Babcock's strategic themes using keyword similarity.
    """

    def __init__(
        self,
        babcock_themes: Dict[str, Dict],
        min_similarity: float = 0.01,
        theme_thresholds: Optional[Dict[str, float]] = None,
    ):
        """
        Args:
            babcock_themes: Dictionary of themes with keywords and metadata.
            min_similarity: Minimum cosine similarity required to assign a theme.
        """
        self.babcock_themes = babcock_themes
        self.min_similarity = min_similarity
        self.theme_thresholds = {**DEFAULT_THEME_THRESHOLDS, **(theme_thresholds or {})}
        self.topic_theme_mapping: Dict[str, Dict] = {}
        self._vectorizer = TfidfVectorizer()
        logger.info(
            "Theme Mapper initialized with %d themes (default threshold=%.3f)",
            len(babcock_themes),
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
        for theme_name, theme_data in self.babcock_themes.items():
            score = self.calculate_keyword_similarity(topic_keywords, theme_data.get("keywords", []))
            scores[theme_name] = score

        best_theme = max(scores, key=scores.get) if scores else "Other"
        best_score = scores.get(best_theme, 0.0)

        threshold = self.theme_thresholds.get(best_theme, self.min_similarity)

        if best_score < threshold:
            return "Other", best_score, scores
        return best_theme, best_score, scores

    def create_theme_mapping(self, topic_model) -> Dict[str, Dict]:
        """
        Build mapping from BERTopic model to Babcock themes.
        """
        logger.info("=" * 80)
        logger.info("MAPPING TOPICS TO BABCOCK THEMES")
        logger.info("=" * 80)

        topic_info = topic_model.get_topic_info()
        mapping: Dict[str, Dict] = {}

        for _, row in topic_info.iterrows():
            topic_id = row["Topic"]
            if topic_id == -1:
                continue  # Skip outlier cluster

            keywords = topic_model.get_topic(topic_id)
            theme, confidence, all_scores = self.map_topic_to_theme(topic_id, keywords)

            mapping[str(topic_id)] = {
                "theme": theme,
                "confidence": float(confidence),
                "all_scores": {k: float(v) for k, v in all_scores.items()},
                "keywords": [word for word, _ in keywords[:10]],
                "count": int(row.get("Count", 0)),
            }

            logger.debug("Topic %s -> %s (confidence %.3f)", topic_id, theme, confidence)

        self.topic_theme_mapping = mapping
        self._log_mapping_summary()
        return mapping

    def _log_mapping_summary(self) -> None:
        """Log summary statistics of the mapping."""
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
    from config.themes import BABCOCK_THEMES

    logger.info("=" * 80)
    logger.info("THEME MAPPING")
    logger.info("=" * 80)

    topic_model = BERTopic.load(BERTOPIC_MODEL_PATH)
    mapper = ThemeMapper(BABCOCK_THEMES)

    mapper.create_theme_mapping(topic_model)
    mapper.identify_cross_theme_topics(threshold=0.6)
    mapper.save_mapping(TOPIC_MAPPING_PATH)

    logger.info("Theme mapping complete.")


if __name__ == "__main__":
    main()
