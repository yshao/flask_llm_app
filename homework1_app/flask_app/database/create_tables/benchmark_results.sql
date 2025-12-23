-- Author: AI Agent Benchmark System
-- Purpose: Store benchmark execution results for tracking and analysis

CREATE TABLE IF NOT EXISTS benchmark_results (
    result_id           SERIAL PRIMARY KEY,
    test_id             integer       NOT NULL,
    execution_timestamp timestamp     DEFAULT CURRENT_TIMESTAMP,
    agent_response      text          NOT NULL,  -- Actual response from the agent
    expected_response   text          NOT NULL,  -- Expected response for comparison
    passed              boolean       NOT NULL,  -- Test passed or failed
    execution_time_ms   integer       DEFAULT NULL,  -- Response time in milliseconds
    error_message       text          DEFAULT NULL,  -- Error details if test failed
    metadata            json          DEFAULT NULL,  -- Additional data (token usage, model version, etc.)

    -- Foreign key constraint
    FOREIGN KEY (test_id) REFERENCES benchmark_test_cases(test_id) ON DELETE CASCADE
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_results_test_id ON benchmark_results(test_id);
CREATE INDEX IF NOT EXISTS idx_results_timestamp ON benchmark_results(execution_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_results_passed ON benchmark_results(passed);

-- Create composite index for time-based pass/fail analysis
CREATE INDEX IF NOT EXISTS idx_results_timestamp_passed ON benchmark_results(execution_timestamp DESC, passed);
