drop table if exists single_domain_clients;

create table single_domain_clients(
       ip inet,
       domain varchar(255),
       count int,
       lastseen timestamp,
       UNIQUE (ip,domain)
);
CREATE INDEX single_domain_clients_ip ON single_domain_clients(ip);
CREATE INDEX single_domain_clients_domain ON single_domain_clients(domain);
