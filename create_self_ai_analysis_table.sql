-- Create the self_ai_analysis_ticker table
-- This table stores AI analysis results for individual stock tickers

CREATE TABLE IF NOT EXISTS self_ai_analysis_ticker (
    insertion_time  timestamp NOT NULL,
    analysis_event_date  date NOT NULL,
    company_ticker   VARCHAR(10) NOT NULL,
    analysis_type VARCHAR(10),
    text_analysis TEXT,
    grade FLOAT,
    model VARCHAR(20),
    weights VARCHAR(400),
    prompt_tokens INT,
    execution_tokens INT,
    test_ind TINYINT(1),
    PRIMARY KEY (insertion_time, analysis_event_date, company_ticker)
);

-- Add unique index to prevent duplicate entries for same ticker and date
ALTER TABLE self_ai_analysis_ticker
ADD UNIQUE INDEX ux_ticker_event_date (analysis_event_date, company_ticker);

-- Add indexes for better query performance
CREATE INDEX idx_company_ticker ON self_ai_analysis_ticker(company_ticker);
CREATE INDEX idx_analysis_type ON self_ai_analysis_ticker(analysis_type);
CREATE INDEX idx_analysis_event_date ON self_ai_analysis_ticker(analysis_event_date);
CREATE INDEX idx_test_ind ON self_ai_analysis_ticker(test_ind); 

