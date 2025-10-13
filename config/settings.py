"""
Configuration settings for Babcock Research Trends Analysis
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAlex API Configuration
OPENALEX_EMAIL = os.getenv('OPENALEX_EMAIL', 'param.pat01@gmail.com')

# Analysis Date Range for Papers
START_DATE = datetime(2018, 1, 1)  # Expanded from 2020 for more papers
ANALYSIS_END_DATE = datetime(2024, 12, 31)

# Institution name variants for better OpenAlex resolution
INSTITUTION_SYNONYMS = {
    "University of Melbourne": ["The University of Melbourne", "Melbourne University", "UniMelb"],
    "University of Sydney": ["The University of Sydney", "Sydney University", "USYD"],
    "University of Queensland": ["The University of Queensland", "UQ"],
    "University of New South Wales": ["UNSW Sydney", "UNSW", "The University of New South Wales"],
    "Australian National University": ["ANU", "The Australian National University"],
    "RMIT University": ["RMIT", "Royal Melbourne Institute of Technology"],
}

# Australasian Universities and their OpenAlex IDs
# Note: IDs are placeholders - collector resolves actual IDs dynamically from OpenAlex API
ALL_UNIVERSITIES = {
    "University of Melbourne": "I145311948",
    "University of Sydney": "I145311949", 
    "University of Queensland": "I145311950",
    "Monash University": "I145311951",
    "University of New South Wales": "I145311952",
    "Australian National University": "I145311953",
    "University of Western Australia": "I145311954",
    "University of Adelaide": "I145311955",
    "RMIT University": "I145311992",
    "University of Technology Sydney": "I145311956",
    "Queensland University of Technology": "I145311957",
    "University of Auckland": "I145311958",
    "University of Otago": "I145311959",
    "University of Canterbury": "I145311960",
    "Massey University": "I145311961",
    "Victoria University of Wellington": "I145311962",
    "Auckland University of Technology": "I145311963",
    "University of Waikato": "I145311964",
    "Lincoln University": "I145311965",
    "University of Tasmania": "I145311966",
    "Griffith University": "I145311967",
    "Deakin University": "I145311968",
    "La Trobe University": "I145311969",
    "Swinburne University of Technology": "I145311970",
    "University of South Australia": "I145311971",
    "Macquarie University": "I145311972",
    "University of Newcastle": "I145311973",
    "Curtin University": "I145311974",
    "University of Wollongong": "I145311975",
    "Flinders University": "I145311976",
    "Bond University": "I145311977",
    "James Cook University": "I145311978",
    "University of Southern Queensland": "I145311979",
    "Central Queensland University": "I145311980",
    "Edith Cowan University": "I145311981",
    "Murdoch University": "I145311982",
    "University of the Sunshine Coast": "I145311983",
    "Charles Darwin University": "I145311984",
    "University of New England": "I145311985",
    "Southern Cross University": "I145311986",
    "Federation University Australia": "I145311987",
    "Australian Catholic University": "I145311989",
    "University of Notre Dame Australia": "I145311990",
    "Torrens University Australia": "I145311991"
}

# File Paths
RAW_PAPERS_CSV = "data/raw/papers_raw.csv"
PROCESSED_PAPERS_CSV = "data/processed/papers_processed.csv"
METADATA_CSV = "data/processed/metadata.csv"
EMBEDDINGS_PATH = "data/processed/embeddings.npy"
BERTOPIC_MODEL_PATH = "models/bertopic_model.pkl"
TOPICS_OVER_TIME_CSV = "data/processed/topics_over_time.csv"
TOPIC_MAPPING_PATH = "data/processed/topic_mapping.json"
TREND_ANALYSIS_PATH = "data/processed/trend_analysis.json"
RESULTS_CSV = "data/exports/results.csv"
DASHBOARD_DATA_JSON = "data/exports/dashboard_data.json"

# Analysis Parameters
MIN_ABSTRACT_LENGTH = 50
MAX_PAPERS_PER_UNIVERSITY = 1000
NR_TIME_BINS = 10
MIN_RELEVANCE_SCORE = 5  # 5% minimum relevance (was 0); allows more papers while filtering noise
TOPIC_MODEL_PARAMS = {
    'min_topic_size': 5,  # Reduced from 10 for smaller dataset (133 papers)
    'min_cluster_size': 5,  # Reduced from 15
    'min_samples': 3,  # Reduced from 5
    'metric': 'euclidean',
    'cluster_selection_method': 'eom'
}

# Dashboard Configuration
DASHBOARD_TITLE = "Research Trend Analyzer"
DASHBOARD_DESCRIPTION = "Analysis of research trends across Australasian universities"