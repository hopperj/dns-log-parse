drop table if exists domain_counts;

create table domain_counts(
       domain varchar(255),
       count INT,
       UNIQUE (domain)
);
ALTER TABLE domain_counts ADD INDEX (domain);
