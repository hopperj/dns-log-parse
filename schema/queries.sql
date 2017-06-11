DROP TABLE IF EXISTS queries;

CREATE TABLE queries(
       timestamp timestamp,
       client inet,
       port int,
       domain varchar,
       query varchar,
       class char(5),
       type char(5),
       recursive char(5),
       dns varchar,
       server inet
);

CREATE INDEX queries_timestamp ON queries(timestamp DESC);
CREATE INDEX queries_client ON queries(client);
CREATE INDEX queries_query ON queries(query);
CREATE INDEX queries_server ON queries(server);
