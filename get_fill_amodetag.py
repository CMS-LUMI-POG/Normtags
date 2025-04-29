#!/usr/bin/env python

# A simple script (based on get_recentfill) to get the accelerator mode for a given fill.

from sqlalchemy import *
from configparser import ConfigParser
import argparse
import base64

known_amodetagids = {1: "PROTPHYS",
                     2: "IONPHYS",
                     3: "PAPHYS"}

def get_fill_amodetag(con, fillnum):
    q = "select amodetagid from cms_lumi_prod.lhcfill where fillnum=:fillnum"
    binddict = { 'fillnum':fillnum }
    r = con.execute(q, binddict)
    return r.first()[0]

def parseservicemap(authfile):
    '''
    parse service config ini file
    output: {servicealias:[protocol,user,passwd,descriptor]}
    '''
    result={}
    parser = ConfigParser()
    parser.read(authfile)
    for s in parser.sections():
        protocol = parser.get(s,'protocol')
        user = parser.get(s,'user')
        passwd = parser.get(s,'pwd')
        descriptor = parser.get(s,'descriptor')
        result[s] = [protocol,user,passwd,descriptor]
    return result

if __name__=='__main__':
    aparser = argparse.ArgumentParser(prog='get_fill_amodetag.py',
                                      formatter_class=argparse.RawDescriptionHelpFormatter,
                                      description='Get the accelerator mode tag for a given fill.')
    aparser.add_argument('-c', '--connect', required=False, default='online', help='DB service name')
    aparser.add_argument('-p', '--authpath', required=False, default='/brildata/db/db.ini', help='Authentication ini file')
    aparser.add_argument('-f', '--fill', required=True, help='Fill number to fetch', type=int)

    args = aparser.parse_args()
    servicealias=args.connect
    servicemap = parseservicemap(args.authpath)
    user = servicemap[servicealias][1]
    passwd = base64.b64decode(servicemap[servicealias][2]).decode('UTF-8')
 
    descriptor = servicemap[servicealias][3]
    
    connecturl = 'oracle+cx_oracle://%s:%s@%s'%(user,passwd,descriptor)
    e = create_engine(connecturl,max_identifier_length=128)
    con = e.connect()
   
    tagid = get_fill_amodetag(con,args.fill)
    if tagid in known_amodetagids:
        print(known_amodetagids[tagid])
    else:
        print(tagid)
