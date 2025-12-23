CREATE TABLE IF NOT EXISTS users (
user_id         SERIAL PRIMARY KEY,
role            varchar(10)  NOT NULL,
email           varchar(100) NOT NULL UNIQUE,
password        varchar(256) NOT NULL
);