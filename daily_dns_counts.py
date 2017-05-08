#!/bin/python3

import pymysql.cursors
import json
import logging
import click
import os
import datetime
import shutil
import numpy as np
import warnings
import pprint
import geoip2.database
from glob import glob


warnings.filterwarnings("ignore")




log_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

pp = pprint.PrettyPrinter(indent=2)


    
class Config:
    def __init__(self):
        pass


@click.group(invoke_without_command=True)
@click.option('--log-level', default='debug')
@click.option('--log', default=False)
@click.option('--db-uri', required=True)
@click.option('--fake', is_flag=True)
@click.pass_context
def run(ctx, log_level, log, db_uri, fake):
    ctx.obj = Config()
    log_level = log_levels[log_level]

    logging.getLogger(__name__)
    if log:
        logging.basicConfig(filename=log, filemode='a', format='%(asctime)s %(levelname)\
        s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S', level=log_level)
    else:
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S', level=log_level)

    ctx.obj.fake = fake
    
    db_uri = json.loads(db_uri)

    ctx.obj.db_uri = db_uri
    
    # Connect to the database
    db_con = pymysql.connect( **db_uri  )
    db_cur = db_con.cursor()

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    
    q = "INSERT IGNORE INTO daily_counts(date, count) VALUES('{:%Y-%m-%d}',(SELECT COUNT(client) from query WHERE DATE(timestamp)='{:%Y-%m-%d}'));".format(yesterday, yesterday)
    db_cur.execute(q)

    # Track how many times each domain has been queried
    q = "REPLACE into domain_counts(domain, count) select domain, count(domain) from query group by domain;"
    db_cur.execute(q)

    # Track all clients who request only a single site
    q = "REPLACE INTO single_domain_clients(ip, domain, count, lastseen) select client, max(query), count(query), max(timestamp) from query group by client having count(distinct(query))=1;"
    db_cur.execute(q)

    # Track all clients who have only made a single query
    q = "REPLACE INTO single_query_clients(ip, domain, lastseen) SELECT client, max(query), max(timestamp) from query group by client having count(distinct(query))=1 and COUNT(client)=1"
    db_cur.execute(q)

    
    #import pprint
    #print(yesterday)
    #print(q)
    #pprint.pprint(db_cur.fetchall())

    if fake:
        db_con.rollback()
    else:
        db_con.commit()
    db_con.close()



if __name__ == '__main__':
    run()    
    
