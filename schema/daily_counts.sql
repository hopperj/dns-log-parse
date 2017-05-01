drop table if exists daily_counts;

create table daily_counts(
       date DATE,
       count INT,
       UNIQUE (date,count)
);
ALTER TABLE daily_counts ADD INDEX (date);
