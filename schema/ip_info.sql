drop table if exists ip_info;


create table ip_info(
       ip inet,
       count int,
       lastseen timestamp
);

CREATE UNiQUE INDEX ip_info_ip ON ip_info(ip);
