SET SCHEMA 'project';

CREATE TABLE tf_idf
(
    word_id INT NOT NULL,
    publication_id INT NOT NULL,
    tf_idf DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (word_id, publication_id)
);


with terms_in_document as (select publication_id, sum(count)::float as c from word_in_text GROUP BY publication_id),
tf as (SELECT publication_id, word_id, wt.count/(select c from terms_in_document WHERE publication_id = wt.publication_id) as tf from word_in_text as wt),
documents_count as (select count(1)::float as c from publication),
documents_with_term as (select word_id, count(1) as c from word_in_text GROUP BY word_id),
idf as (select id, (select c from documents_count)/(select c from documents_with_term where word_id = kw.id) as idf from keyword as kw)
insert INTO tf_idf (word_id, publication_id, tf_idf) select tf.word_id, tf.publication_id, tf.tf*idf.idf from tf left join idf on tf.word_id = idf.id;

create index tf_idf_word_id ON project.tf_idf USING HASH (word_id);
create index tf_idf_publication_id ON project.tf_idf USING HASH (publication_id);