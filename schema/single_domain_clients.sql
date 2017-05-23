drop table if exists single_domain_clients;

create table single_domain_clients(
       ip varchar(15),
       domain varchar(255),
       count int,
       lastseen timestamp,
       UNIQUE (ip,domain)
);
ALTER TABLE single_domain_clients ADD INDEX (ip);
ALTER TABLE single_domain_clients ADD INDEX (domain);
