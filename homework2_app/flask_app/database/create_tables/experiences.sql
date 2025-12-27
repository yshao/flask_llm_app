CREATE TABLE IF NOT EXISTS experiences (
experience_id   SERIAL PRIMARY KEY,
position_id     integer NOT NULL,
name            varchar(500) NOT NULL,
description     varchar(500) NOT NULL,
hyperlink       varchar(500) DEFAULT NULL,
start_date      date DEFAULT NULL,
end_date        date DEFAULT NULL,
embedding       vector(768)   DEFAULT NULL,
FOREIGN KEY (position_id) REFERENCES positions(position_id)
);

CREATE INDEX IF NOT EXISTS experiences_embedding_idx
ON experiences USING ivfflat (embedding vector_cosine_ops);
