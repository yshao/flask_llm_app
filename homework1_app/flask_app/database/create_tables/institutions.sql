CREATE TABLE IF NOT EXISTS institutions (
inst_id        SERIAL PRIMARY KEY,
type           varchar(100)  NOT NULL,
name           varchar(100)  NOT NULL,
department     varchar(100)  DEFAULT NULL,
address        varchar(100)  DEFAULT NULL,
city           varchar(100)  DEFAULT NULL,
state          varchar(100)  DEFAULT NULL,
zip            varchar(10)   DEFAULT NULL
);