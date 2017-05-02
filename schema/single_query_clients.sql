drop table if exists single_query_clients;

create table single_query_clients(
       ip varchar(15),
       domain varchar(255),
       UNIQUE (ip,domain)
);
ALTER TABLE single_query_clients ADD INDEX (ip);
ALTER TABLE single_query_clients ADD INDEX (domain);
