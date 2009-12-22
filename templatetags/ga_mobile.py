import os

from django.conf import settings
from django import template
from random import randint
from urllib import quote_plus

register = template.Library()

@register.simple_tag
def ga_mobile(request):
    """
    Returns the image link for tracking this mobile request.
    
    Retrieves two configurations from django.settings:
    
    GA_MOBILE_PATH: path (including leading /) to location of your tracking CGI.
    GA_MOBILE_ACCOUNT: your GA mobile account number such as MO-XXXXXX-XX
    
    Note: the host for the request is by default the same as the HTTP_HOST of the request.
    Override this by setting GA_MOBILE_HOST in settings.
    """

    ga_mobile_path = settings.GA_MOBILE_PATH
    ga_mobile_account = settings.GA_MOBILE_ACCOUNT    
    r = str(randint(0, 0x7fffffff))

    if hasattr(settings, 'GA_MOBILE_HOST'):
        host = settings.GA_MOBILE_HOST
    else:
        host = request.META.get('HTTP_HOST', 'localhost')
    referer = quote_plus(request.META.get('HTTP_REFERER', ''))
    path = quote_plus(request.META.get('REQUEST_URI', ''))
    
    src = 'http://' + host + ga_mobile_path + \
        "?utmac=" + ga_mobile_account + \
        "&utmn=" + r + \
        "&utmr=" + referer + \
        "&utmp=" + path + \
        "&guid=ON"

    return '<img src="%s" width="1" height="1">' % src