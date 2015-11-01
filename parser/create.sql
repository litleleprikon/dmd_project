CREATE TABLE temp_word
(
    word VARCHAR NOT NULL,
    count INT DEFAULT 0 NOT NULL,
    id SERIAL PRIMARY KEY NOT NULL,
    document INT NOT NULL
);
CREATE INDEX word_index ON temp_word (word);
