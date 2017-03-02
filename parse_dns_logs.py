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
    
    db_uri = json.loads(db_uri)

    ctx.obj.db_uri = db_uri
    ctx.obj.geoip_loc = geoip
    
    # Connect to the database
    db_con = pymysql.connect( **db_uri  )
    db_cur = db_con.cursor()
    new_dns_in = move_log_data(ctx, dns_in, dns_archive)
    logging.debug('Using new fname: %s'%new_dns_in)
    data = parse_log( ctx, new_dns_in )
    archive(ctx, new_dns_in)
    logging.debug('Data archived')
    if not data:
        logging.info('Log is empty')
    else:
        logging.debug('Found %d data'%len(data))
        insert_data( ctx, data, db_cur )
        logging.debug('data inserted')
        firewall_traffic( ctx, data, db_cur )
        logging.debug('data filtering complete')

    geoip_update(ctx, db_cur, data)
    logging.debug('geoip update complete')
    if fake:
        db_con.rollback()
    else:
        db_con.commit()
    db_con.close()





# TODO: Hardcoded for security and to make sure I don't ban known legit clients -- for use while developing only.
goodclients = [
    '198.48.212.10',
    '142.134.23.233',
    '156.34.16.90',
    '156.34.207.182',
    '50.241.143.0/24',
    '172.20.2.93'
]


    
def firewall_traffic(ctx, data, db_cur):
    '''
    All of this is disabled at the moment. Blocking an IP during an amplification attack doesn't do anything
    because the IP is being spoofed. This code should be changed to detecting sites being looked up for amplification
    attacks, and blocking it in the zone files.
    '''
    return
    records = {}
    domains = {}
    time_delta = data[-1]['timestamp'] - data[0]['timestamp']

    for dat in data:
        if dat['client'] not in records:
            records[ dat['client'] ] = {}
        if dat['domain'] not in records[ dat['client'] ]:
            records[ dat['client'] ][ dat['domain'] ] = 0
        if dat['domain'] not in domains:
            #print('Adding:',dat['domain'])
            domains[dat['domain']] = 0

        domains[dat['domain']] += 1
        records[ dat['client'] ][ dat['domain'] ] += 1

    print('Calculating ....')
    total_queries = len(data)

    vals = [ v for v in domains.values() ]
    average = np.average(vals)
    std = np.std(vals)
    pp.pprint(domains)
    norm_domains = { k:v/total_queries for k,v in domains.items() }
    print('Average:',average)
    print('STD:',std)
    print('\n')

    for ip in records:
        if len(records[ip]) == 1:
            for domain in records[ip]:
                if records[ip][domain]/time_delta.total_seconds() > 1.0:
                    if ip in goodclients:
                        logging.critical('Tried to block goodclient %s!'%ip)
                    else:
                        logging.info('--> Blocking: %s, %s, %s'%(ip,domain,records[ip][domain]))
                        q = "REPLACE INTO firewall(ip, status, timestamp, domain) VALUES('%s', '%s', '%s', '%s')"%(
                            ip,
                            'deny',
                            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            domain
                        )

                        #print(q)
                        
                        if not ctx.obj.fake:
                            db_cur.execute(q)
                        
    
    pp.pprint(records)
        

def insert_data(ctx, data, db_cur):
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
    logging.debug('Beginning insertmany command')
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
    logging.debug('insert many complete')

        
def parse_log(ctx, fname):
    with open(fname) as f:
        raw_data = [ l.split() for l in f.readlines() ]
    data = [
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

    return data




def archive( ctx, dns_archive):
    os.system('gzip '+dns_archive)

def move_log_data(ctx, dns_in, dns_archive):
    #return dns_in
    new_fname = os.path.join(
        dns_archive,
        datetime.datetime.strftime( datetime.datetime.now(), "%Y-%m-%dT%H-%M-%S_dns_record.log" )
    )
    if ctx.obj.fake:
        new_fname = '/tmp/dns_query.log'
        shutil.copy(dns_in, new_fname)
    else:
        #os.rename(dns_in, new_fname)
        shutil.copy(dns_in, new_fname)
        os.system('truncate -s 0 '+dns_in)
        #os.system('touch '+dns_in)
        #os.system('chown bind:bind '+dns_in)
    return new_fname




def geoip_update(ctx, db_cur, data):
    reader = geoip2.database.Reader(ctx.obj.geoip_loc)
    # Check all unique IP addresses in the data (set ensures uniqueness)
    for result in set([ d['client'] for d in data ]):
        try:
            res = reader.city(result)
            country = res.country.name.encode('latin-1', 'replace')
            city = res.city.name.encode('latin-1', 'replace')
        except:
            country = None
            city = None

        db_cur.execute('REPLACE INTO ip_info(ip, country, city) VALUES(%s,%s,%s)',(result,country, city))





if __name__ == '__main__':
    run()    
    
