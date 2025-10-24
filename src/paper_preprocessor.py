"""
Paper Preprocessor for Babcock Research Trends Analysis
Handles text preprocessing, cleaning, and preparation for topic modeling
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import List, Dict, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
import string

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperPreprocessor:
    """
    Preprocess research papers for topic modeling and analysis
    """
    
    def __init__(self, min_abstract_length: int = 50):
        """
        Initialize preprocessor
        
        Args:
            min_abstract_length: Minimum length for abstracts to keep
        """
        self.min_abstract_length = min_abstract_length
        self.stop_words = set()
        self.lemmatizer = None
        self._setup_nltk()
        
        logger.info(f"PaperPreprocessor initialized with min_abstract_length={min_abstract_length}")
    
    def _setup_nltk(self):
        """Setup NLTK resources"""
        if not NLTK_AVAILABLE:
            logger.warning("NLTK not available. Using basic preprocessing.")
            self.stop_words = set()
            self.lemmatizer = None
            return
            
        try:
            # Download required NLTK data
            nltk.download('stopwords', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('omw-1.4', quiet=True)
            
            # Setup stopwords and lemmatizer
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            
            # Add custom stopwords
            custom_stopwords = {
                'paper', 'study', 'research', 'analysis', 'results', 'conclusion',
                'abstract', 'introduction', 'method', 'methodology', 'approach',
                'system', 'model', 'algorithm', 'technique', 'framework',
                'data', 'dataset', 'experiment', 'evaluation', 'performance',
                'application', 'implementation', 'development', 'design',
                'using', 'used', 'use', 'based', 'proposed', 'presented',
                'shows', 'demonstrates', 'indicates', 'suggests', 'reveals'
            }
            self.stop_words.update(custom_stopwords)
            
        except Exception as e:
            logger.warning(f"NLTK setup failed: {e}. Using basic preprocessing.")
            self.stop_words = set()
            self.lemmatizer = None
    
    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess text
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize_and_lemmatize(self, text: str) -> List[str]:
        """
        Tokenize and lemmatize text
        
        Args:
            text: Cleaned text
            
        Returns:
            List of processed tokens
        """
        if not text:
            return []
        
        try:
            if NLTK_AVAILABLE and self.lemmatizer:
                # Tokenize
                tokens = word_tokenize(text)
                
                # Remove stopwords and short words
                tokens = [
                    token for token in tokens 
                    if token not in self.stop_words 
                    and len(token) > 2
                    and token not in string.punctuation
                ]
                
                # Lemmatize if available
                if self.lemmatizer:
                    tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
                
                return tokens
            else:
                # Fallback to simple split when NLTK is not available
                words = text.split()
                tokens = [
                    word for word in words 
                    if len(word) > 2
                    and word not in string.punctuation
                ]
                return tokens
            
        except Exception as e:
            logger.debug(f"Tokenization failed: {e}")
            # Fallback to simple split
            return [word for word in text.split() if len(word) > 2]
    
    def preprocess_abstracts(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess abstracts in the dataframe
        
        Args:
            df: DataFrame with papers data
            
        Returns:
            DataFrame with preprocessed abstracts
        """
        logger.info("Preprocessing abstracts...")
        
        df_processed = df.copy()
        
        # Clean abstracts
        df_processed['abstract_clean'] = df_processed['abstract'].apply(self.clean_text)
        
        # Filter out short abstracts
        initial_count = len(df_processed)
        df_processed = df_processed[
            df_processed['abstract_clean'].str.len() >= self.min_abstract_length
        ]
        filtered_count = len(df_processed)
        
        logger.info(f"Filtered abstracts: {initial_count} -> {filtered_count} "
                   f"({filtered_count/initial_count*100:.1f}% kept)")
        
        # Tokenize and lemmatize
        df_processed['tokens'] = df_processed['abstract_clean'].apply(
            lambda x: self.tokenize_and_lemmatize(x)
        )
        
        # Create processed text for topic modeling
        df_processed['processed_text'] = df_processed['tokens'].apply(
            lambda tokens: ' '.join(tokens)
        )
        
        # Remove papers with no tokens
        df_processed = df_processed[df_processed['tokens'].str.len() > 0]
        
        logger.info(f"Final processed papers: {len(df_processed)}")
        
        return df_processed
    
    def extract_keywords(self, df: pd.DataFrame, top_n: int = 20) -> Dict[str, List[str]]:
        """
        Extract top keywords for each university
        
        Args:
            df: DataFrame with processed papers
            top_n: Number of top keywords to extract per university
            
        Returns:
            Dictionary mapping university names to top keywords
        """
        logger.info(f"Extracting top {top_n} keywords per university...")
        
        university_keywords = {}
        
        for university in df['university'].unique():
            uni_papers = df[df['university'] == university]
            
            # Combine all processed text for this university
            all_text = ' '.join(uni_papers['processed_text'].tolist())
            
            if not all_text.strip():
                continue
            
            # Use TF-IDF to find important terms
            try:
                vectorizer = TfidfVectorizer(
                    max_features=1000,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.8
                )
                
                tfidf_matrix = vectorizer.fit_transform([all_text])
                feature_names = vectorizer.get_feature_names_out()
                scores = tfidf_matrix.toarray()[0]
                
                # Get top keywords
                top_indices = np.argsort(scores)[-top_n:][::-1]
                top_keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
                
                university_keywords[university] = top_keywords
                
            except Exception as e:
                logger.warning(f"Keyword extraction failed for {university}: {e}")
                university_keywords[university] = []
        
        return university_keywords
    
    def get_processing_stats(self, df: pd.DataFrame) -> Dict:
        """
        Get statistics about the preprocessing
        
        Args:
            df: Processed DataFrame
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'total_papers': len(df),
            'papers_with_abstracts': df['abstract'].notna().sum(),
            'papers_after_filtering': len(df[df['abstract_clean'].str.len() >= self.min_abstract_length]),
            'avg_abstract_length': df['abstract_clean'].str.len().mean(),
            'avg_tokens_per_paper': df['tokens'].str.len().mean(),
            'universities_count': df['university'].nunique(),
            'date_range': f"{df['date'].min()} to {df['date'].max()}" if 'date' in df.columns else "N/A"
        }
        
        return stats
    
    def save_processed_data(self, df: pd.DataFrame, filepath: str) -> None:
        """
        Save processed data to CSV
        
        Args:
            df: Processed DataFrame
            filepath: Output file path
        """
        # Convert lists to strings for CSV storage
        df_save = df.copy()
        df_save['tokens'] = df_save['tokens'].apply(lambda x: '|'.join(x) if x else '')
        
        df_save.to_csv(filepath, index=False)
        logger.info(f"  Saved processed data to: {filepath}")


# ==================== USAGE EXAMPLE ====================

def main():
    """
    Example usage of PaperPreprocessor
    """
    import pandas as pd
    from config.settings import RAW_PAPERS_CSV, PROCESSED_PAPERS_CSV
    
    # Load raw data
    try:
        df = pd.read_csv(RAW_PAPERS_CSV)
        logger.info(f"Loaded {len(df)} papers from {RAW_PAPERS_CSV}")
    except FileNotFoundError:
        logger.error(f"Raw data file not found: {RAW_PAPERS_CSV}")
        logger.info("Please run the data collection first.")
        return
    
    # Initialize preprocessor
    preprocessor = PaperPreprocessor(min_abstract_length=50)
    
    # Preprocess abstracts
    df_processed = preprocessor.preprocess_abstracts(df)
    
    # Extract keywords
    keywords = preprocessor.extract_keywords(df_processed, top_n=20)
    
    # Get statistics
    stats = preprocessor.get_processing_stats(df_processed)
    
    # Save processed data
    preprocessor.save_processed_data(df_processed, PROCESSED_PAPERS_CSV)
    
    # Print summary
    print("\n" + "="*80)
    print("PREPROCESSING SUMMARY")
    print("="*80)
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print(f"\nTop keywords per university:")
    for uni, kw in list(keywords.items())[:3]:  # Show first 3 universities
        print(f"{uni}: {', '.join(kw[:10])}")  # Show first 10 keywords


if __name__ == "__main__":
    main()
