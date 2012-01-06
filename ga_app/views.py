from ga import send_request_to_google_analytics, get_random_number, get_visitor_id, get_ip, VERSION, COOKIE_NAME, COOKIE_PATH, COOKIE_USER_PERSISTENCE, GIF_DATA

import httplib2
import time
from urllib import unquote, quote

from urllib import unquote, quote
from django.http import HttpResponse

def track(request):
    """
    Track a page view, updates all the cookies and campaign tracker,
     makes a server side request to Google Analytics and writes the transparent
     gif byte data to the response.
    """
    response = HttpResponse()
    
    time_tup = time.localtime(time.time() + COOKIE_USER_PERSISTENCE)
    
    # set some useful items in environ: 
    x_utmac = request.GET.get('x_utmac', None)
    
    domain = request.META.get('HTTP_HOST', '')
            
    # Get the referrer from the utmr parameter, this is the referrer to the
    # page that contains the tracking pixel, not the referrer for tracking
    # pixel.    
    document_referer = request.GET.get("utmr", "")
    if not document_referer or document_referer == "0":
        document_referer = "-"
    else:
        document_referer = unquote(document_referer)

    document_path = request.GET.get('utmp', "")
    if document_path:
        document_path = unquote(document_path)

    account = request.GET.get('utmac', '')      
    user_agent = request.META.get("HTTP_USER_AGENT", '')    

    # Try and get visitor cookie from the request.
    cookie = request.COOKIES.get(COOKIE_NAME, None)

    visitor_id = get_visitor_id(request.META.get("HTTP_X_DCMGUID", ''), account, user_agent, cookie)
    
    utm_gif_location = "http://www.google-analytics.com/__utm.gif"

    for utmac in [account, x_utmac]:
        if not utmac:
            continue # ignore empty utmacs
        # Construct the gif hit url.
        utm_url = utm_gif_location + "?" + \
                "utmwv=" + VERSION + \
                "&utmn=" + get_random_number() + \
                "&utmhn=" + quote(domain) + \
                "&utmsr=" + request.GET.get('utmsr', '') + \
                "&utme=" + request.GET.get('utme', '') + \
                "&utmr=" + quote(document_referer) + \
                "&utmp=" + quote(document_path) + \
                "&utmac=" + utmac + \
                "&utmcc=__utma%3D999.999.999.999.999.1%3B" + \
                "&utmvid=" + visitor_id + \
                "&utmip=" + get_ip(request.META.get("REMOTE_ADDR",''))
        send_request_to_google_analytics(utm_url, request.META)
    
    # add the cookie to the response.
    response.set_cookie(COOKIE_NAME, value=visitor_id, path=COOKIE_PATH)
    # If the debug parameter is on, add a header to the response that contains
    # the url that was used to contact Google Analytics.
    if request.GET.get('utmdebug', False):
        response['X-GA-MOBILE-URL'] = utm_url
    
    response_headers =[('Content-Type', 'image/gif'),                                     
                         ('Cache-Control', 'private, no-cache, no-cache=Set-Cookie, proxy-revalidate'),
                         ('Pragma', 'no-cache'),
                         ('Expires', 'Wed, 17 Sep 1975 21:32:10 GMT')]
    for header in response_headers:
        key, value = header
        response[key] = value
    response.content = GIF_DATA
    
    return response