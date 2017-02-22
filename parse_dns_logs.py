#!/bin/python3





import pymysql.cursors
import json
import logging
import click
import os
import datetime
import shutil

import warnings
warnings.filterwarnings("ignore")




log_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}



@click.group(invoke_without_command=True)
@click.option('--log-level', default='debug')
@click.option('--log', default=False)
@click.option('--db-uri', required=True)
@click.option('--dns-in', default='/var/log/named/queries.log', required=False)
@click.option('--dns-archive', default='/data/dns_log_backups/', required=False)
@click.pass_context
def run(ctx, log_level, log, db_uri, dns_in, dns_archive):
    log_level = log_levels[log_level]

    logging.getLogger(__name__)
    if log:
        logging.basicConfig(filename=log, filemode='a', format='%(asctime)s %(levelname)\
        s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S', level=log_level)
    else:
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y\
        -%m-%dT%H:%M:%S', level=log_level)

    
    db_uri = json.loads(db_uri)

    
    # Connect to the database
    with pymysql.connect( **db_uri  ) as db_cur:
        new_dns_in = move_log_data(dns_in, dns_archive)
        logging.debug('Using new fname: %s'%new_dns_in)
        data = parse_log( new_dns_in )
        logging.debug('Found %d data'%len(data))
        insert_data( data, db_cur )

def insert_data(data, db_cur):
    d = data[0]
    q = "insert into query(timestamp, client, port, domain, query, class, type, recursive, dns) VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s')"%(
        d['timestamp'],
        d['client'],
        d['port'],
        d['domain'],
        d['query'],
        d['class'],
        d['type'],
        d['recursive'],
        d['dns']
    )
    
    db_cur.executemany(
        "INSERT IGNORE query(timestamp, client, port, domain, query, class, type, recursive, dns) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s);",
        [
            (
                d['timestamp'],
                d['client'],
                d['port'],
                d['domain'],
                d['query'],
                d['class'],
                d['type'],
                d['recursive'],
                d['dns']
            )
            for d in data
        ]
    )

        
def parse_log(fname):
    with open(fname) as f:
        raw_data = [ l.split() for l in f.readlines() ]
    data = [
        {
            'timestamp':datetime.datetime.strptime(e[0]+' '+e[1].split('.')[0], '%d-%b-%Y %H:%M:%S'),
            'client':e[3].split('#')[0],
            'port':int(e[3].split('#')[-1]),
            'domain':e[4][1:-2],
            'query':e[6],
            'class':e[7],
            'type':e[8],
            'recursive':e[9],
            'dns':e[10][1:-1]
        }
        for e in raw_data
    ]

    return data

        
def move_log_data(dns_in, dns_archive):
    new_fname = os.path.join(
        dns_archive,
        datetime.datetime.strftime( datetime.datetime.now(), "%Y-%m-%dT%H-%M-%S_dns_record.log" )
    )
    #shutil.copy(dns_in, new_fname)
    os.rename(dns_in, new_fname)
    return new_fname

    


if __name__ == '__main__':
    run()    
    
