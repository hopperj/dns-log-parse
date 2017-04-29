drop table if exists ip_info;


create table ip_info(
       ip varchar(15),
       count int,
       lastseen datetime
);

create unique index ip_info_ip on ip_info(ip);


/*
insert into ip_info values('127.0.0.1',1,NOW()) on duplicate key update count=count+1, lastseen=NOW();
*/
