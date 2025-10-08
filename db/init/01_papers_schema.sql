-- Simplified Database Schema for OpenAlex Paper Ingestion
-- Focus: Paper storage and metadata only (no ML/topics)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Papers table: Simplified core paper metadata
CREATE TABLE IF NOT EXISTS papers (
    openalex_id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    publication_date DATE NOT NULL,
    year INTEGER NOT NULL,
    
    -- Publication details
    journal VARCHAR(500),
    doi VARCHAR(255),
    
    -- Institution/University info
    university VARCHAR(500),
    
    -- Research area/field
    concepts JSONB,  -- OpenAlex concepts with scores
    primary_field VARCHAR(255),
    
    -- Metadata
    is_open_access BOOLEAN DEFAULT false,
    
    -- Sync tracking
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
CREATE INDEX IF NOT EXISTS idx_papers_pub_date ON papers(publication_date);
CREATE INDEX IF NOT EXISTS idx_papers_university ON papers(university);
CREATE INDEX IF NOT EXISTS idx_papers_concepts ON papers USING gin(concepts);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_papers_updated_at ON papers;
CREATE TRIGGER update_papers_updated_at
    BEFORE UPDATE ON papers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Ingestion state tracking
CREATE TABLE IF NOT EXISTS ingestion_state (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- e.g., 'openalex'
    last_sync_date TIMESTAMP,
    last_paper_date DATE,
    total_papers_fetched INTEGER DEFAULT 0,
    status VARCHAR(50),  -- 'in_progress', 'completed', 'failed'
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingestion logs for debugging and monitoring
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id SERIAL PRIMARY KEY,
    ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50),
    papers_added INTEGER,
    papers_updated INTEGER,
    papers_skipped INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    query_params JSONB,
    duration_seconds INTEGER
);

-- Comments for documentation
COMMENT ON TABLE papers IS 'Simplified research papers table with core metadata from OpenAlex';
COMMENT ON COLUMN papers.concepts IS 'OpenAlex concepts/topics with relevance scores';
COMMENT ON COLUMN papers.openalex_id IS 'Primary key - unique OpenAlex identifier';
COMMENT ON TABLE ingestion_state IS 'Tracks the state of data ingestion from external sources';
COMMENT ON TABLE ingestion_logs IS 'Audit log of all ingestion runs';
