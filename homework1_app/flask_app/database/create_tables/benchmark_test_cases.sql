-- Author: AI Agent Benchmark System
-- Purpose: Store benchmark test cases for agent evaluation

CREATE TABLE IF NOT EXISTS benchmark_test_cases (
    test_id             SERIAL PRIMARY KEY,
    test_name           varchar(200)  NOT NULL,
    test_category       varchar(100)  NOT NULL,  -- 'chat_functionality', 'resume_query', 'page_context'
    input_message       text          NOT NULL,  -- The user query to test
    expected_output_type varchar(50)  NOT NULL,  -- 'contains_text', 'sql_result', 'exact_match'
    expected_output     text          NOT NULL,  -- Ground truth for comparison
    page_context        json          DEFAULT NULL,  -- Optional page content for context-aware tests
    active              boolean       DEFAULT TRUE,  -- Enable/disable specific tests
    created_at          timestamp     DEFAULT CURRENT_TIMESTAMP,
    updated_at          timestamp     DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster category-based queries
CREATE INDEX IF NOT EXISTS idx_test_cases_category ON benchmark_test_cases(test_category);

-- Create index for active test filtering
CREATE INDEX IF NOT EXISTS idx_test_cases_active ON benchmark_test_cases(active);
