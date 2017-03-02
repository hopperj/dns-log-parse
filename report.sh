
select query, count(query) as q from query group by query order by q desc limit 25;



select query.client,query.count,ip_info.country,ip_info.city  from (select query.client,count(query.client) as count from query join ip_info on query.client=ip_info.ip group by client order by count desc) as query join ip_info on query.client=ip_info.ip order by count desc;
