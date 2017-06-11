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

import psycopg2
import psycopg2.extras
import psycopg2.pool
import ipgetter


IP = ipgetter.myip()

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
@click.option('--dns-in', default='/var/log/named/queries.log', required=True)
@click.option('--dns-archive', default='/data/dns_log_backups/', required=True)
@click.option('--geoip', required=True)
@click.option('--fake', is_flag=True)
@click.pass_context
def run(ctx, log_level, log, db_uri, dns_in, dns_archive, geoip, fake):
    ctx.obj = Config()
    log_level = log_levels[log_level]

    logging.getLogger(__name__)
    if log:
        logging.basicConfig(filename=log, filemode='a', format='%(asctime)s %(levelname)\
        s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S', level=log_level)
    else:
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S', level=log_level)

    ctx.obj.fake = fake
    ctx.obj.db_uri = db_uri
    ctx.obj.geoip_loc = geoip
    
    # Connect to the database
    con = psycopg2.connect(db_uri)
    cur = con.cursor()

    data = move_log_data(ctx, dns_in, dns_archive)
    logging.debug('Will now process %d entries'%len(data))
    #logging.debug('Using new fname: %s'%new_dns)
    #data = parse_log( ctx, raw_data )
    #archive(ctx, new_dns)

    if not data:
        logging.info('Log is empty')
    else:
        logging.debug('Found %d data'%len(data))
        insert_data( ctx, data, cur )

    geoip_update(ctx, cur, data)

    if fake:
        con.rollback()
    else:
        con.commit()
    con.close()




def insert_data(ctx, data, db_cur):

    batch_size = 1000
    for i in range(0, len(data), batch_size):
        args_str = ','.join(
            "('{}','{}',{},'{}','{}','{}','{}','{}','{}','{}')".format(
                d['timestamp'],
                d['client'],
                d['port'],
                d['domain'],
                d['query'],
                d['class'],
                d['type'],
                d['recursive'],
                d['dns'],
                IP
            )
            for d in data[i:i+batch_size]
        )
        q = "INSERT into queries(timestamp, client, port, domain, query, class, type, recursive, dns, server) VALUES "
        db_cur.execute(q + args_str) 
        
    '''
    db_cur.executemany(
        "INSERT into queries(timestamp, client, port, domain, query, class, type, recursive, dns, server) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",
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
                d['dns'],
                IP
            )
            for d in data
        ]
    )
    '''
    
    ips = set([ e['client'] for e in data])
    logging.info('Doing IP count updates')
    for ip in ips:        
        db_cur.execute("INSERT INTO ip_info VALUES('%s', 1, NOW()) ON CONFLICT (ip) DO UPDATE SET count=ip_info.count+%d, lastseen=NOW();"%(ip, len([1 for e in data if e['client']==ip])))
        
def parse_log(ctx, fname):
    pass


def archive( ctx, dns_archive):
    os.system('gzip '+dns_archive)

def move_log_data(ctx, dns_in, dns_archive):
    new_fname = os.path.join(
        dns_archive,
        datetime.datetime.strftime( datetime.datetime.now(), "%Y-%m-%dT%H-%M-%S_dns_record.log" )
    )
    if not ctx.obj.fake:
        new_f = open( new_fname, 'w' )

    data = []
    fnames = glob(dns_in)
    logging.debug('Will extract from %d files'%len(fnames))
    #pp.pprint(fnames)
    # Itterate through all files
    for fname in fnames:
        # Open files for reading
        with open(fname) as f:
            # Dump file contents to archive file
            logging.info('Extracting %s'%fname)
            if not ctx.obj.fake:
                new_f.write(f.read())
            f.seek(0)
            raw_data = [ l.split() for l in f.readlines() ]
            # Truncate main log file, delete others
            if not ctx.obj.fake:
                if fname.endswith('.log'):
                    os.system('truncate -s 0 '+fname)
                else:
                    os.system('rm '+fname)

            data += [
                {
                    'timestamp':datetime.datetime.strptime(e[0]+' '+e[1], '%d-%b-%Y %H:%M:%S.%f'),
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

    # Close and archive file
    if not ctx.obj.fake:
        new_f.close()
        archive(ctx, new_fname)

    return data




def geoip_update(ctx, db_cur, data):
    reader = geoip2.database.Reader(ctx.obj.geoip_loc)
    # Check all unique IP addresses in the data (set ensures uniqueness)
    for result in set([ d['client'] for d in data ]):
        try:
            res = reader.city(result)
            country = res.country.name.encode('utf8', 'ignore').decode('utf8')
            city = res.city.name.encode('utf8', 'ignore').decode('utf8')

            db_cur.execute('REPLACE INTO geo_info(ip, country, city) VALUES(%s,%s,%s)',(result,country, city))
        except:
            country = None
            city = None





if __name__ == '__main__':
    run()    
    
