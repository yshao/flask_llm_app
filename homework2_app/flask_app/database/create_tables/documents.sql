-- Documents table for web-crawled content
-- Stores chunks of web pages with 768-dim embeddings for semantic search

CREATE TABLE IF NOT EXISTS documents (
    document_id   SERIAL PRIMARY KEY,
    url           varchar(500) NOT NULL,
    title         varchar(500) NOT NULL,
    chunk_text    text NOT NULL,
    chunk_index   integer NOT NULL,
    embedding     vector(768) DEFAULT NULL,
    created_at    timestamp DEFAULT CURRENT_TIMESTAMP
);

-- IVFFlat index on embedding for fast semantic search
CREATE INDEX IF NOT EXISTS documents_embedding_idx
ON documents USING ivfflat (embedding vector_cosine_ops);

-- Index on url for faster joins with experiences table
CREATE INDEX IF NOT EXISTS documents_url_idx
ON documents (url);
