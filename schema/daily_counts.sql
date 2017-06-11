drop table if exists daily_counts;

create table daily_counts(
       date DATE,
       count INT,
       UNIQUE (date,count),
       server inet
);
CREATE INDEX daily_counts_date ON daily_counts(date DESC);
