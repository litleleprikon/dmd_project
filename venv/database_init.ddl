CREATE TABLE author
(
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT NOT NULL
);
CREATE UNIQUE INDEX index_author_id ON author (id);
CREATE TABLE keywords
(
    id INTEGER PRIMARY KEY NOT NULL,
    word TEXT NOT NULL
);
CREATE TABLE publications
(
    id INTEGER PRIMARY KEY NOT NULL,
    title TEXT NOT NULL,
    year INTEGER NOT NULL,
    source TEXT,
    publisher INTEGER NOT NULL,
    description TEXT NOT NULL,
    isbn TEXT
);
CREATE TABLE publisher
(
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT NOT NULL
);
