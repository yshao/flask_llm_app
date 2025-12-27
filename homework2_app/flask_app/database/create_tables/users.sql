CREATE TABLE IF NOT EXISTS users (
user_id         SERIAL PRIMARY KEY,
role            varchar(10)  NOT NULL,
email           varchar(100) NOT NULL UNIQUE,
password        varchar(256) NOT NULL,
embedding       vector(768)   DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS users_embedding_idx
ON users USING ivfflat (embedding vector_cosine_ops);
