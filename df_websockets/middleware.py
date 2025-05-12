# ##############################################################################
#  This file is part of df_websockets                                          #
#                                                                              #
#  Copyright (C) 2020 Matthieu Gallet <github@19pouces.net>                    #
#  All Rights Reserved                                                         #
#                                                                              #
#  You may use, distribute and modify this code under the                      #
#  terms of the (BSD-like) CeCILL-B license.                                   #
#                                                                              #
#  You should have received a copy of the CeCILL-B license with                #
#  this file. If not, please visit:                                            #
#  https://cecill.info/licences/Licence_CeCILL-B_V1-en.txt (English)           #
#  or https://cecill.info/licences/Licence_CeCILL-B_V1-fr.txt (French)         #
#                                                                              #
# ##############################################################################
import logging
from urllib.parse import quote_plus

from django.conf import settings
from django.contrib.sessions.backends.base import VALID_KEY_CHARS
from django.core.exceptions import DisallowedHost
from django.http import HttpRequest, HttpResponse
from django.utils.crypto import get_random_string
from django.utils.deprecation import MiddlewareMixin

from df_websockets import ws_settings
from df_websockets.constants import WEBSOCKET_KEY_COOKIE_NAME, WEBSOCKET_URL_COOKIE_NAME

logger = logging.getLogger("django.request")


class WebsocketMiddleware(MiddlewareMixin):
    ws_windowkey_get_parameter = "dfwskey"
    ws_windowkey_header_name = "DFWSKEY"

    def process_request(self, request: HttpRequest):
        request.window_key = None
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            header = "HTTP_%s" % self.ws_windowkey_header_name
            request.window_key = request.META.get(header)
            if not request.window_key and WEBSOCKET_KEY_COOKIE_NAME in request.COOKIES:
                request.window_key = request.COOKIES[WEBSOCKET_KEY_COOKIE_NAME]
        if not request.window_key:
            request.window_key = get_random_string(32, VALID_KEY_CHARS)
        request.has_websocket_topics = False

    # noinspection PyMethodMayBeStatic
    def process_response(self, request: HttpRequest, response: HttpResponse):
        # noinspection PyUnresolvedReferences
        if not request.has_websocket_topics:
            return response
        # noinspection PyUnresolvedReferences
        window_key = request.window_key
        netloc = request.get_host()
        use_ssl = request.is_secure()
        scheme = "ws"
        if use_ssl:
            scheme = "wss"
        ws_url = f"{scheme}://{netloc}{ws_settings.WEBSOCKET_URL}"
        kwargs = {
            "max_age": 86400,
            "domain": settings.CSRF_COOKIE_DOMAIN,
            "path": settings.CSRF_COOKIE_PATH,
            "secure": use_ssl,
            "httponly": False,
            "samesite": settings.CSRF_COOKIE_SAMESITE,
        }
        response.set_cookie(WEBSOCKET_URL_COOKIE_NAME, quote_plus(ws_url), **kwargs)
        response.set_cookie(WEBSOCKET_KEY_COOKIE_NAME, window_key, **kwargs)
        return response
