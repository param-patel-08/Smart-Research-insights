"""
Emerging Topics Detector
Identifies emerging research topics and generates human-readable labels using ChatGPT
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from bertopic import BERTopic
import openai
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class EmergingTopicsDetector:
    """
    Detect emerging research topics and generate descriptive labels
    """
    
    def __init__(self, 
                 bertopic_model_path: str,
                 papers_df: pd.DataFrame,
                 topic_mapping: Dict,
                 openai_api_key: str = None):
        """
        Args:
            bertopic_model_path: Path to trained BERTopic model
            papers_df: DataFrame with papers and topic assignments
            topic_mapping: Topic to theme mapping
            openai_api_key: OpenAI API key (optional, reads from env if not provided)
        """
        self.model = BERTopic.load(bertopic_model_path)
        self.papers_df = papers_df.copy()
        self.topic_mapping = topic_mapping
        
        # Setup OpenAI
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        else:
            logger.warning("No OpenAI API key found. Labels will use keywords only.")
        
        logger.info(f"Initialized with {len(self.papers_df)} papers and {len(topic_mapping)} topics")
    
    def calculate_emergingness_score(self, 
                                     topic_id: int,
                                     recency_weight: float = 0.4,
                                     growth_weight: float = 0.4,
                                     volume_weight: float = 0.2) -> Dict:
        """
        Calculate emergingness score for a topic based on:
        1. Recency: How recent are the papers?
        2. Growth: Is the topic growing rapidly?
        3. Volume: How many papers?
        
        Args:
            topic_id: BERTopic topic ID
            recency_weight: Weight for recency component (default 0.4)
            growth_weight: Weight for growth rate component (default 0.4)
            volume_weight: Weight for volume component (default 0.2)
            
        Returns:
            Dict with score components and final emergingness score
        """
        topic_papers = self.papers_df[self.papers_df['topic_id'] == topic_id].copy()
        
        if len(topic_papers) == 0:
            return {
                'topic_id': topic_id,
                'emergingness_score': 0.0,
                'recency_score': 0.0,
                'growth_score': 0.0,
                'volume_score': 0.0,
                'paper_count': 0,
                'avg_citations': 0.0,
                'latest_date': None
            }
        
        # Convert dates
        topic_papers['date'] = pd.to_datetime(topic_papers['date'])
        latest_date = pd.to_datetime(self.papers_df['date']).max()
        
        # 1. RECENCY SCORE (0-1)
        # Papers in last 12 months get higher scores
        topic_papers['months_old'] = (latest_date - topic_papers['date']).dt.days / 30
        
        # Exponential decay: papers lose relevance over time
        recency_scores = np.exp(-topic_papers['months_old'] / 12)  # Half-life of 12 months
        recency_score = recency_scores.mean()
        
        # 2. GROWTH SCORE (0-1)
        # Calculate quarterly growth rate
        topic_papers['quarter'] = topic_papers['date'].dt.to_period('Q')
        quarterly_counts = topic_papers.groupby('quarter').size().sort_index()
        
        if len(quarterly_counts) >= 4:
            # Compare last 2 quarters vs previous 2 quarters
            recent_avg = quarterly_counts.iloc[-2:].mean()
            older_avg = quarterly_counts.iloc[-4:-2].mean()
            
            if older_avg > 0:
                growth_rate = (recent_avg - older_avg) / older_avg
                # Normalize to 0-1 range (cap at 200% growth)
                growth_score = min(max(growth_rate / 2 + 0.5, 0), 1)
            else:
                growth_score = 1.0 if recent_avg > 0 else 0.0
        elif len(quarterly_counts) >= 2:
            # Simple comparison of last vs first quarter
            growth_rate = (quarterly_counts.iloc[-1] - quarterly_counts.iloc[0]) / max(quarterly_counts.iloc[0], 1)
            growth_score = min(max(growth_rate / 2 + 0.5, 0), 1)
        else:
            growth_score = 0.5  # Neutral if insufficient data
        
        # 3. VOLUME SCORE (0-1)
        # Normalize by percentile in all topics
        all_topic_counts = self.papers_df.groupby('topic_id').size()
        volume_percentile = (all_topic_counts <= len(topic_papers)).sum() / len(all_topic_counts)
        volume_score = volume_percentile
        
        # CALCULATE FINAL SCORE
        emergingness_score = (
            recency_weight * recency_score +
            growth_weight * growth_score +
            volume_weight * volume_score
        )
        
        # Additional metrics
        avg_citations = topic_papers['citations'].mean() if 'citations' in topic_papers.columns else 0.0
        latest_date = topic_papers['date'].max()
        
        return {
            'topic_id': topic_id,
            'emergingness_score': emergingness_score,
            'recency_score': recency_score,
            'growth_score': growth_score,
            'volume_score': volume_score,
            'paper_count': len(topic_papers),
            'avg_citations': avg_citations,
            'latest_date': latest_date.strftime('%Y-%m-%d') if latest_date else None,
            'growth_rate': (growth_rate * 100) if 'growth_rate' in locals() else 0.0
        }
    
    def identify_emerging_topics(self, 
                                 min_emergingness: float = 0.5,
                                 top_n: int = 20) -> pd.DataFrame:
        """
        Identify emerging topics across all themes
        
        Args:
            min_emergingness: Minimum emergingness score (0-1)
            top_n: Return top N emerging topics
            
        Returns:
            DataFrame with emerging topics and scores
        """
        logger.info("\nCalculating emergingness scores for all topics...")
        
        emerging_topics = []
        
        for topic_id in self.papers_df['topic_id'].unique():
            if topic_id == -1:  # Skip outliers
                continue
            
            scores = self.calculate_emergingness_score(topic_id)
            
            # Add theme and keywords
            topic_id_str = str(topic_id)
            if topic_id_str in self.topic_mapping:
                scores['theme'] = self.topic_mapping[topic_id_str]['theme']
                scores['sub_theme'] = self.topic_mapping[topic_id_str].get('sub_theme', None)
                scores['keywords'] = self.topic_mapping[topic_id_str]['keywords'][:10]
            else:
                scores['theme'] = 'Unknown'
                scores['sub_theme'] = None
                scores['keywords'] = []
            
            if scores['emergingness_score'] >= min_emergingness:
                emerging_topics.append(scores)
        
        # Convert to DataFrame and sort
        df = pd.DataFrame(emerging_topics)
        df = df.sort_values('emergingness_score', ascending=False).head(top_n)
        
        logger.info(f"Found {len(df)} emerging topics (threshold: {min_emergingness})")
        
        return df
    
    def _filter_noisy_keywords(self, keywords: List[str]) -> List[str]:
        """
        Remove noisy/generic keywords that don't add meaning
        """
        noise_words = {
            'google', 'scholar', 'researchgate', 'pubmed', 'arxiv',
            'et', 'al', 'doi', 'http', 'https', 'www',
            'paper', 'study', 'research', 'analysis', 'approach',
            'method', 'results', 'data', 'using', 'based',
            'review', 'systematic', 'meta', 'analysis',
            'journal', 'conference', 'proceedings', 'article',
            'abstract', 'introduction', 'conclusion', 'discussion'
        }
        
        filtered = []
        for kw in keywords:
            kw_lower = kw.lower()
            # Skip if it's a noise word or very short
            if kw_lower not in noise_words and len(kw) > 2:
                # Skip if it contains URL patterns
                if not any(x in kw_lower for x in ['http', 'www', '.com', '.org']):
                    filtered.append(kw)
        
        return filtered[:10]  # Return max 10 clean keywords
    
    def generate_topic_label_with_gpt(self, 
                                     keywords: List[str],
                                     theme: str,
                                     sub_theme: str = None,
                                     paper_count: int = 0,
                                     growth_rate: float = 0.0) -> str:
        """
        Use ChatGPT to generate a human-readable label for an emerging topic
        
        Args:
            keywords: List of topic keywords from BERTopic
            theme: Parent theme
            sub_theme: Sub-theme if available
            paper_count: Number of papers in topic
            growth_rate: Growth rate percentage
            
        Returns:
            Human-readable topic label
        """
        if not self.openai_api_key:
            logger.error("⚠️ NO OPENAI API KEY! Set OPENAI_API_KEY in .env file")
            logger.error("   Labels will be poor quality without GPT")
            return f"[No API Key] {' '.join(keywords[:2])}"
        
        try:
            # Filter out noisy keywords
            clean_keywords = self._filter_noisy_keywords(keywords)
            
            if len(clean_keywords) < 3:
                # If too few clean keywords, use original
                clean_keywords = keywords[:10]
            
            keywords_str = ", ".join(clean_keywords[:8])
            
            # Build context
            domain = theme.replace('_', ' ').title()
            sub_context = f"\nSub-area: {sub_theme.replace('_', ' ')}" if sub_theme else ""
            
            prompt = f"""You are a research analyst identifying emerging topics in academic research.

Domain: {domain}{sub_context}
Keywords from research papers: {keywords_str}
Publication volume: {paper_count} papers
Growth trend: {growth_rate:.0f}% growth rate

Task: Create a single, clear research topic label (4-8 words maximum) that:
1. Describes the SPECIFIC research focus (not generic)
2. Uses technical/domain terminology appropriately
3. Is actionable for strategic decisions
4. Sounds natural and professional

Examples of GOOD labels:
- "Deep Learning for Medical Image Segmentation"
- "Blockchain-based Supply Chain Traceability"
- "Quantum Computing for Drug Discovery"
- "Edge AI for IoT Security"

Examples of BAD labels:
- "Machine Learning Applications" (too generic)
- "AI + Neural Networks + Deep Learning" (keyword list)
- "Research on Data Analysis Methods" (too vague)

Generate ONLY the topic label (4-8 words), nothing else. No quotes, no explanations."""

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert research analyst who creates precise, meaningful labels for emerging research topics. You never just list keywords."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=60
            )
            
            label = response.choices[0].message.content.strip()
            
            # Clean up the label
            label = label.strip('"').strip("'").strip('`').strip()
            
            # Remove any "Topic:" or "Label:" prefixes
            for prefix in ['Topic:', 'Label:', 'Research Topic:', 'Emerging Topic:']:
                if label.startswith(prefix):
                    label = label[len(prefix):].strip()
            
            # Validate label quality
            if len(label.split()) < 3:
                logger.warning(f"Label too short: '{label}', regenerating...")
                # Try again with more explicit prompt
                label = f"{domain}: {' '.join(clean_keywords[:3])}"
            
            logger.info(f"✓ Generated: '{label}'")
            
            return label
            
        except Exception as e:
            logger.error(f"❌ GPT API Error: {e}")
            # Better fallback
            clean_kw = self._filter_noisy_keywords(keywords)
            if len(clean_kw) >= 2:
                return f"{theme.replace('_', ' ')}: {' & '.join(clean_kw[:2])}"
            else:
                return f"{theme.replace('_', ' ')} Research Topic"
    
    def generate_labels_for_emerging_topics(self, 
                                           emerging_df: pd.DataFrame,
                                           use_gpt: bool = True) -> pd.DataFrame:
        """
        Generate human-readable labels for all emerging topics using GPT
        
        Args:
            emerging_df: DataFrame from identify_emerging_topics()
            use_gpt: Whether to use GPT for label generation (default True)
            
        Returns:
            DataFrame with added 'topic_label' column
        """
        if not self.openai_api_key:
            logger.error("\n" + "="*80)
            logger.error("⚠️  ERROR: NO OPENAI API KEY FOUND!")
            logger.error("="*80)
            logger.error("Topic labels will be poor quality without GPT.")
            logger.error("Please add OPENAI_API_KEY to your .env file.")
            logger.error("="*80 + "\n")
        
        logger.info(f"\n🤖 Generating labels for {len(emerging_df)} emerging topics using GPT...")
        logger.info("This may take 30-60 seconds...\n")
        
        labels = []
        
        for idx, row in emerging_df.iterrows():
            logger.info(f"[{idx+1}/{len(emerging_df)}] Processing topic {row['topic_id']}...")
            
            if use_gpt and self.openai_api_key:
                label = self.generate_topic_label_with_gpt(
                    keywords=row['keywords'],
                    theme=row['theme'],
                    sub_theme=row['sub_theme'],
                    paper_count=row['paper_count'],
                    growth_rate=row.get('growth_rate', 0.0)
                )
            else:
                # Poor fallback
                clean_kw = self._filter_noisy_keywords(row['keywords'])
                if len(clean_kw) >= 2:
                    label = f"{row['theme'].replace('_', ' ')}: {' & '.join(clean_kw[:2])}"
                else:
                    label = f"Topic {row['topic_id']}"
            
            labels.append(label)
        
        emerging_df['topic_label'] = labels
        
        logger.info("\n✓ All labels generated successfully!\n")
        
        return emerging_df
    
    def save_emerging_topics(self, emerging_df: pd.DataFrame, filepath: str):
        """Save emerging topics to JSON"""
        output = emerging_df.to_dict(orient='records')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved emerging topics to {filepath}")


def main():
    """
    Example usage
    """
    from config.settings import BERTOPIC_MODEL_PATH, PROCESSED_PAPERS_CSV
    
    logger.info("="*80)
    logger.info("EMERGING TOPICS DETECTOR")
    logger.info("="*80)
    
    # Load data
    logger.info("\nLoading data...")
    papers_df = pd.read_csv(PROCESSED_PAPERS_CSV)
    
    with open('data/processed/topic_mapping.json', 'r') as f:
        topic_mapping = json.load(f)
    
    logger.info(f"Loaded {len(papers_df)} papers")
    logger.info(f"Loaded {len(topic_mapping)} topic mappings")
    
    # Initialize detector
    detector = EmergingTopicsDetector(
        bertopic_model_path=BERTOPIC_MODEL_PATH,
        papers_df=papers_df,
        topic_mapping=topic_mapping
    )
    
    # Identify emerging topics
    emerging_topics = detector.identify_emerging_topics(
        min_emergingness=0.5,
        top_n=20
    )
    
    logger.info(f"\nTop {len(emerging_topics)} Emerging Topics:")
    for _, topic in emerging_topics.iterrows():
        logger.info(f"\nTopic {topic['topic_id']} ({topic['theme']})")
        logger.info(f"  Emergingness: {topic['emergingness_score']:.3f}")
        logger.info(f"  Papers: {topic['paper_count']}")
        logger.info(f"  Keywords: {', '.join(topic['keywords'][:5])}")
    
    # Generate labels with GPT
    emerging_topics = detector.generate_labels_for_emerging_topics(emerging_topics, use_gpt=True)
    
    logger.info("\n" + "="*80)
    logger.info("EMERGING TOPICS WITH LABELS:")
    logger.info("="*80)
    
    for _, topic in emerging_topics.iterrows():
        logger.info(f"\n📌 {topic['topic_label']}")
        logger.info(f"   Theme: {topic['theme'].replace('_', ' ')}")
        if topic['sub_theme']:
            logger.info(f"   Sub-theme: {topic['sub_theme'].replace('_', ' ')}")
        logger.info(f"   Emergingness: {topic['emergingness_score']:.3f} ⭐")
        logger.info(f"   Papers: {topic['paper_count']}")
        logger.info(f"   Avg Citations: {topic['avg_citations']:.1f}")
        logger.info(f"   Growth Rate: {topic['growth_rate']:.1f}%")
    
    # Save results
    detector.save_emerging_topics(emerging_topics, 'data/processed/emerging_topics.json')
    
    logger.info("\n✓ Analysis complete!")


if __name__ == "__main__":
    main()
