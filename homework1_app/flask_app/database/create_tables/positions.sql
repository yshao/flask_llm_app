CREATE TABLE IF NOT EXISTS positions (
position_id        SERIAL PRIMARY KEY,
inst_id            integer       NOT NULL,
title              varchar(100)  NOT NULL,
responsibilities   varchar(500)  NOT NULL,
start_date         date          NOT NULL,
end_date           date          DEFAULT NULL,
FOREIGN KEY (inst_id) REFERENCES institutions(inst_id)
);