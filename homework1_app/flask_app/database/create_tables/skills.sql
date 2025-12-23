CREATE TABLE IF NOT EXISTS skills (
skill_id       SERIAL PRIMARY KEY,
experience_id  integer DEFAULT NULL,
name           varchar(200) NOT NULL,
skill_level    integer NOT NULL,
FOREIGN KEY (experience_id) REFERENCES experiences(experience_id)
);