drop table if exists geo_info;


create table geo_info(
       ip    char(15),
       country	char(255),
       city	char(255)
);
ALTER TABLE geo_info ADD INDEX (ip);
ALTER TABLE geo_info ADD INDEX (country);
CREATE UNIQUE index geo_info_ip on geo_info(ip);
