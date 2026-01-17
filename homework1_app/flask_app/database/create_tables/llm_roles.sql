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
    description TEXT,
    system_prompt TEXT,
    instruction TEXT,
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

-- Add comments for documentation
COMMENT ON COLUMN llm_roles.description IS 'Detailed description of the expert role';
COMMENT ON COLUMN llm_roles.system_prompt IS 'System prompt used by the LLM';
COMMENT ON COLUMN llm_roles.instruction IS 'Instruction template for generating responses';

-- Migration script for existing databases (run if table already exists)
-- Uncomment and run this block if updating existing database:
--
-- ALTER TABLE llm_roles ADD COLUMN IF NOT EXISTS description TEXT;
-- ALTER TABLE llm_roles ADD COLUMN IF NOT EXISTS system_prompt TEXT;
-- ALTER TABLE llm_roles ADD COLUMN IF NOT EXISTS instruction TEXT;
-- COMMENT ON COLUMN llm_roles.description IS 'Detailed description of the expert role';
-- COMMENT ON COLUMN llm_roles.system_prompt IS 'System prompt used by the LLM';
-- COMMENT ON COLUMN llm_roles.instruction IS 'Instruction template for generating responses';