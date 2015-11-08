CREATE TABLE author
(
  id   SERIAL PRIMARY KEY NOT NULL,
  name VARCHAR(50)        NOT NULL
);

CREATE TABLE author_of_publication
(
  author_id      INT NOT NULL,
  publication_id INT NOT NULL,
  PRIMARY KEY (publication_id, author_id)
);

CREATE TABLE publication
(
  id         SERIAL PRIMARY KEY NOT NULL,
  title      VARCHAR(500)       NOT NULL,
  year       INT,
  publisher  INT,
  pdf        VARCHAR(2000)      NOT NULL,
  type       INT                NOT NULL,
  abstract   VARCHAR            NOT NULL,
  ar_number  INT,
  doi        VARCHAR(50),
  end_page   INT,
  md_url     VARCHAR(2000),
  part_num   INT,
  start_page INT
);

CREATE TABLE book
(
  isbn       VARCHAR(20)                                                         NOT NULL,
  pub_title  VARCHAR(500)
) INHERITS (publication);
CREATE TABLE conference
(
  affiliation VARCHAR(500)                                                        NOT NULL,
  isbn        VARCHAR(20)                                                         NOT NULL,
  pu_number   INT
) INHERITS (publication);
CREATE TABLE journal
(
  affiliations VARCHAR(500),
  issn         VARCHAR(20)                                                         NOT NULL,
  issue        VARCHAR(15),
  pub_title    VARCHAR(500),
  pu_number    INT,
  volume       INT                                                                 NOT NULL
) INHERITS (publication);
CREATE TABLE keyword
(
  id   SERIAL PRIMARY KEY NOT NULL,
  word VARCHAR            NOT NULL
);

CREATE TABLE publication_type
(
  id   SERIAL PRIMARY KEY NOT NULL,
  name VARCHAR(50)        NOT NULL
);

CREATE TABLE publisher
(
  id   SERIAL PRIMARY KEY NOT NULL,
  name VARCHAR(50)        NOT NULL
);


CREATE TABLE tf_idf
(
  word_id        INT              NOT NULL,
  publication_id INT              NOT NULL,
  tf_idf         DOUBLE PRECISION NOT NULL,
  PRIMARY KEY (word_id, publication_id)
);
CREATE TABLE thesaurus
(
  id   SERIAL PRIMARY KEY NOT NULL,
  word VARCHAR(50)        NOT NULL
);

CREATE TABLE thesaurus_of_publication
(
  publication INT NOT NULL,
  thesaurus   INT NOT NULL,
  PRIMARY KEY (publication, thesaurus)
);
CREATE TABLE "user"
(
  id       SERIAL PRIMARY KEY NOT NULL,
  username VARCHAR(50)        NOT NULL,
  passhash VARCHAR(128)       NOT NULL,
  salt     VARCHAR(32)        NOT NULL,
  email    VARCHAR            NOT NULL
);

CREATE TABLE word_in_text
(
  publication_id INT           NOT NULL,
  word_id        INT           NOT NULL,
  count          INT DEFAULT 0 NOT NULL
);
CREATE INDEX word_index ON keyword USING HASH (word);
ALTER TABLE publication ADD FOREIGN KEY (type) REFERENCES publication_type (id);
ALTER TABLE publication ADD FOREIGN KEY (publisher) REFERENCES publisher (id);
CREATE UNIQUE INDEX unique_doi ON publication (doi);
CREATE UNIQUE INDEX unique_id ON publication_type (id);
CREATE UNIQUE INDEX unique_name ON publication_type (name);
CREATE UNIQUE INDEX "unique_id " ON publisher (id);
CREATE UNIQUE INDEX unique_username ON "user" (username);
CREATE INDEX publication_id_index ON word_in_text USING HASH (publication_id);
CREATE INDEX word_id_index ON word_in_text USING HASH (word_id);
