drop table if exists geo_info;


create table geo_info(
       ip    inet,
       country	char(255),
       city	char(255)
);
CREATE INDEX geo_info_ip ON geo_info(ip);
CREATE INDEX geo_info_country ON geo_info(country);
CREATE UNIQUE INDEX geo_info_unique_ip ON geo_info(ip);



