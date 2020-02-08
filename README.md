# dns-log-parse
Parse Bind9 query log files.

# Dependancies
- pymysql
- click
- numpy
- pprint


# How to run:
`python3 parse_dns_logs.py --db-uri='{"host":"host", "user":"user", "password":"password", "database":"db"}' --dns-in="/var/log/named/queries.log" --dns-archive="/data/dns_log_archive" --log="/path/to/logs/dns-log-parse.log" --geoip /path/to/GeoLite2-City.mmdb`
