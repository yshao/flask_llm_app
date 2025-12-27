-- Author: Prof. MM Ghassemi <ghassem3@msu.edu>
-- Homework 1: LLM Roles Table Schema
-- Stores expert role configurations for multi-expert AI agent system

CREATE TABLE llm_roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(255) UNIQUE NOT NULL,
    domain VARCHAR(500),
    specific_instructions TEXT,
    background_context TEXT,
    few_shot_examples TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster role lookup
CREATE INDEX idx_llm_roles_name ON llm_roles(role_name);
CREATE INDEX idx_llm_roles_active ON llm_roles(is_active);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_llm_roles_updated_at 
    BEFORE UPDATE ON llm_roles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();