from sqlalchemy import *
from ConfigParser import SafeConfigParser
import argparse
import sys
import time
import os, os.path


def get_fillsince(con,minfill=None):
    binddict = {}
    q = "select max(fillnum) from cms_lumi_prod.lhcfill"
    if minfill:
        q = "select fillnum from cms_lumi_prod.lhcfill where fillnum>:minfill"
        binddict = { 'minfill':int(minfill) }
        r = con.execute(q,binddict)
        flist = []
        for f in r:
            flist.append(f['fillnum'])
        return flist
    else:
        r = con.execute(q,{}).fetchone()
        if not r: return 0
        return r[0]

def parseservicemap(authfile):
    '''
    parse service config ini file
    output: {servicealias:[protocol,user,passwd,descriptor]}
    '''
    result={}
    parser = SafeConfigParser()
    parser.read(authfile)
    for s in parser.sections():
        protocol = parser.get(s,'protocol')
        user = parser.get(s,'user')
        passwd = parser.get(s,'pwd')
        descriptor = parser.get(s,'descriptor')
        result[s] = [protocol,user,passwd,descriptor]
    return result

if __name__=='__main__':
    aparser = argparse.ArgumentParser(prog='get_recentfill',
                                      formatter_class=argparse.RawDescriptionHelpFormatter,
                                      description='check fills more recent than a known fill in the brildb')
    aparser.add_argument('-c', '--connect',
                         required = False,
                         default='online',
                         help='dbservicename')
    aparser.add_argument('-p', '--authpath',
                         required = False,
                         default='/brildata/db/db.ini',
                         help='authentication ini file')
    aparser.add_argument('-f', '--lastfill',
                         required = False,
                         help='last known fill. If not given, return the most recent fill in brildb.')

    args = aparser.parse_args()
    servicealias=args.connect
    servicemap = parseservicemap(args.authpath)
    user = servicemap[servicealias][1]
    passwd = servicemap[servicealias][2].decode('base64')
    descriptor = servicemap[servicealias][3]
    
    connecturl = 'oracle+cx_oracle://%s:%s@%s'%(user,passwd,descriptor)
    e = create_engine(connecturl)
    con = e.connect()

    recentfill = get_fillsince(con,args.lastfill)
    print recentfill
    
