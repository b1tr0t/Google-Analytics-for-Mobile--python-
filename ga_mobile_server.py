#!/usr/bin/env python
# encoding: utf-8
"""
server.py

Serves up google analytics 1x1.gif transparent tracking images and notifies Google Analytics of clicks.  

Created by Peter McLachlan on 2009-07-19.
Copyright (c) 2009 Mobify. All rights reserved.
"""

import sys
import os
import getopt
from urlparse import urlparse
from flup.server.fcgi_fork import WSGIServer
from socket import gethostname
from datetime import datetime, timedelta
from ga import track_page_view

from messaging import stdMsg, dbgMsg, errMsg, setDebugging
setDebugging(1)

MINSPARE = 3
MAXSPARE = 7
MAXCHILDREN = 50
MAXREQUESTS = 500
HOST = '127.0.0.1'
PORT = 8009
PIDFILE = '/tmp/g_analytic_server.pid'
HELP_MESSAGE = """

This is some help.

"""

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def gserve(environ, start_response):    
    try:
        response = track_page_view(environ)
    except Exception, e:
        print e
        start_response("503 Service Unavailable", [])
        return ["<h1>Exception loading GA code</h1><p>%s</p>" % str(e)]
    start_response(response['response_code'], response['response_headers'])
    return [response['response_body']]
    
def main(argv=None):
    host = HOST
    port = PORT
    pidfile = PIDFILE
    maxchildren = MAXCHILDREN
    maxrequests = MAXREQUESTS
    minspare = MINSPARE
    maxspare = MAXSPARE
    
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["host=", "port=", 'pidfile=', 'maxchildren=', 
                                                      'maxrequests=', 'minspare=', 'maxspare=', 'help'])
        except getopt.error, msg:
            raise Usage(msg)
        # option processing
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(HELP_MESSAGE)
            elif "--host" == option:
                host = value
            elif "--port" == option:
                port = int(value)
            elif "--pidfile" == option:
                pidfile = value
            elif "--maxchildren" == option:
                maxchildren = int(value)
            elif "--maxrequests" == option:
                maxrequests = int(value)
            elif "--minspare" == option:
                minspare = int(value)
            elif "--maxspare" == option:
                maxspare = int(value)
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return -2
    
    try:
        f = open(pidfile, 'w')
        f.write(str(os.getpid()) + '\n')
        f.close()
    except IOError, e:
        print "!! Error writing to pid file, check pid file path: %s" % pidfile
        return -1
    
    try:
        WSGIServer(gserve, bindAddress=(host, port), minSpare=minspare, maxSpare=maxspare, maxChildren=maxchildren, maxRequests=maxrequests).run()
    except Exception, e:
        print "!! WSGIServer raised exception" 
        print e
    
    
if __name__ == "__main__":
    sys.exit(main())    