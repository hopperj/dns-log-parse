drop table if exists single_query_clients;

create table single_query_clients(
       ip inet,
       domain varchar(255),
       lastseen    timestamp,
       UNIQUE (ip,domain)
);
CREATE INDEX single_query_clients_ip ON single_query_clients(ip);
CREATE INDEX single_query_clients_domain ON single_query_clients(domain);
