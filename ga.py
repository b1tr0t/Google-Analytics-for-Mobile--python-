"""
Python implementation of ga.php.  
"""
import re
from hashlib import md5
from random import randint
import struct
import httplib2
import time
from urllib import unquote, quote
from Cookie import SimpleCookie, CookieError
from messaging import stdMsg, dbgMsg, errMsg, setDebugging
import uuid

try:
    # The mod_python version is more efficient, so try importing it first.
    from mod_python.util import parse_qsl
except ImportError:
    from cgi import parse_qsl

VERSION = "4.4sh"
COOKIE_NAME = "__utmmobile"
COOKIE_PATH = "/"
COOKIE_USER_PERSISTENCE = 63072000

GIF_DATA = reduce(lambda x,y: x + struct.pack('B', y), 
                  [0x47,0x49,0x46,0x38,0x39,0x61,
                   0x01,0x00,0x01,0x00,0x80,0x00,
                   0x00,0x00,0x00,0x00,0xff,0xff,
                   0xff,0x21,0xf9,0x04,0x01,0x00,
                   0x00,0x00,0x00,0x2c,0x00,0x00,
                   0x00,0x00,0x01,0x00,0x01,0x00, 
                   0x00,0x02,0x01,0x44,0x00,0x3b], '')

# WHITE GIF:
# 47 49 46 38 39 61 
# 01 00 01 00 80 ff 
# 00 ff ff ff 00 00 
# 00 2c 00 00 00 00 
# 01 00 01 00 00 02 
# 02 44 01 00 3b                                       

# TRANSPARENT GIF:
# 47 49 46 38 39 61 
# 01 00 01 00 80 00 
# 00 00 00 00 ff ff 
# ff 21 f9 04 01 00 
# 00 00 00 2c 00 00 
# 00 00 01 00 01 00 
# 00 02 01 44 00 3b                  

def get_ip(remote_address):
    # dbgMsg("remote_address: " + str(remote_address))
    if not remote_address:
        return ""
    matches = re.match('^([^.]+\.[^.]+\.[^.]+\.).*', remote_address)
    if matches:
        return matches.groups()[0] + "0"
    else:
        return ""

def get_visitor_id(guid, account, user_agent, cookie):
    """
     // Generate a visitor id for this hit.
     // If there is a visitor id in the cookie, use that, otherwise
     // use the guid if we have one, otherwise use a random number.
    """
    if cookie:
        return cookie
    message = ""
    if guid:
        # Create the visitor id using the guid.
        message = guid + account
    else:
        # otherwise this is a new user, create a new random id.
        message = user_agent + str(uuid.uuid4())
    md5String = md5(message).hexdigest()
    return "0x" + md5String[:16]

def get_random_number():
    """
    // Get a random number string.
    """
    return str(randint(0, 0x7fffffff))

def write_gif_data():
    """
    // Writes the bytes of a 1x1 transparent gif into the response.

    Returns a dictionary with the following values: 
    
    { 'response_code': '200 OK',
      'response_headers': [(Header_key, Header_value), ...]
      'response_body': 'binary data'
    }
    """
    response = {'response_code': '204 No Content', 
                'response_headers': [('Content-Type', 'image/gif'),                                     
                                     ('Cache-Control', 'private, no-cache, no-cache=Set-Cookie, proxy-revalidate'),
                                     ('Pragma', 'no-cache'),
                                     ('Expires', 'Wed, 17 Sep 1975 21:32:10 GMT'),
                                     ],
                # 'response_body': GIF_DATA,
                'response_body': '',
                }
    return response

def send_request_to_google_analytics(utm_url, environ):
    """
  // Make a tracking request to Google Analytics from this server.
  // Copies the headers from the original request to the new one.
  // If request containg utmdebug parameter, exceptions encountered
  // communicating with Google Analytics are thown.    
    """
    http = httplib2.Http()    
    try:
        resp, content = http.request(utm_url, 
                                     "GET", 
                                     headers={'User-Agent': environ.get('HTTP_USER_AGENT', 'Unknown'),
                                              'Accepts-Language:': environ.get("HTTP_ACCEPT_LANGUAGE",'')}
                                     )
        # dbgMsg("success")            
    except HttpLib2Error, e:
        errMsg("fail: %s" % utm_url)            
        if environ['GET'].get('utmdebug'):
            raise Exception("Error opening: %s" % utm_url)
        else:
            pass

        
def parse_cookie(cookie):
    """ borrowed from django.http """
    if cookie == '':
        return {}
    try:
        c = SimpleCookie()
        c.load(cookie)
    except CookieError:
        # Invalid cookie
        return {}

    cookiedict = {}
    for key in c.keys():
        cookiedict[key] = c.get(key).value
    return cookiedict        
        
def track_page_view(environ):
    """
    // Track a page view, updates all the cookies and campaign tracker,
    // makes a server side request to Google Analytics and writes the transparent
    // gif byte data to the response.
    """    
    time_tup = time.localtime(time.time() + COOKIE_USER_PERSISTENCE)
    
    # set some useful items in environ: 
    environ['COOKIES'] = parse_cookie(environ.get('HTTP_COOKIE', ''))
    environ['GET'] = {}
    for key, value in parse_qsl(environ.get('QUERY_STRING', ''), True):
        environ['GET'][key] = value # we only have one value per key name, right? :) 
    x_utmac = environ['GET'].get('x_utmac', None)
    
    domain = environ.get('HTTP_HOST', '')
            
    # Get the referrer from the utmr parameter, this is the referrer to the
    # page that contains the tracking pixel, not the referrer for tracking
    # pixel.    
    document_referer = environ['GET'].get("utmr", "")
    if not document_referer or document_referer == "0":
        document_referer = "-"
    else:
        document_referer = unquote(document_referer)

    document_path = environ['GET'].get('utmp', "")
    if document_path:
        document_path = unquote(document_path)

    account = environ['GET'].get('utmac', '')      
    user_agent = environ.get("HTTP_USER_AGENT", '')    

    # // Try and get visitor cookie from the request.
    cookie = environ['COOKIES'].get(COOKIE_NAME)

    visitor_id = get_visitor_id(environ.get("HTTP_X_DCMGUID", ''), account, user_agent, cookie)
    
    # // Always try and add the cookie to the response.
    cookie = SimpleCookie()
    cookie[COOKIE_NAME] = visitor_id
    morsel = cookie[COOKIE_NAME]
    morsel['expires'] = time.strftime('%a, %d-%b-%Y %H:%M:%S %Z', time_tup) 
    morsel['path'] = COOKIE_PATH

    utm_gif_location = "http://www.google-analytics.com/__utm.gif"

    for utmac in [account, x_utmac]:
        if not utmac:
            continue # ignore empty utmacs
        # // Construct the gif hit url.
        utm_url = utm_gif_location + "?" + \
                "utmwv=" + VERSION + \
                "&utmn=" + get_random_number() + \
                "&utmhn=" + quote(domain) + \
                "&utmsr=" + environ['GET'].get('utmsr', '') + \
                "&utme=" + environ['GET'].get('utme', '') + \
                "&utmr=" + quote(document_referer) + \
                "&utmp=" + quote(document_path) + \
                "&utmac=" + utmac + \
                "&utmcc=__utma%3D999.999.999.999.999.1%3B" + \
                "&utmvid=" + visitor_id + \
                "&utmip=" + get_ip(environ.get("REMOTE_ADDR",''))
        # dbgMsg("utm_url: " + utm_url)    
        send_request_to_google_analytics(utm_url, environ)

    # // If the debug parameter is on, add a header to the response that contains
    # // the url that was used to contact Google Analytics.
    headers = [('Set-Cookie', str(cookie).split(': ')[1])]
    if environ['GET'].get('utmdebug', False):
        headers.append(('X-GA-MOBILE-URL', utm_url))
    
    # Finally write the gif data to the response
    response = write_gif_data()
    response_headers = response['response_headers']
    response_headers.extend(headers)
    return response