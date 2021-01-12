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
from django.core import signing
from django.http import HttpRequest, HttpResponse
from django.utils.crypto import get_random_string
from django.utils.deprecation import MiddlewareMixin

from df_websockets import ws_settings

logger = logging.getLogger("django.request")


def sign_token(session_id, ws_token, user_pk=None):
    signer = signing.Signer(session_id)
    data = "%s:%s" % (ws_token, user_pk)
    signed_token = signer.sign(data)
    return signed_token


def unsign_token(session_id, signed_token):
    signer = signing.Signer(session_id)
    data = signer.unsign(signed_token)
    window_key, __, user_pk = data.partition(":")
    return window_key, user_pk, None


class WebsocketMiddleware(MiddlewareMixin):
    ws_windowkey_get_parameter = "dfwskey"
    ws_windowkey_header_name = "DFWSKEY"

    # noinspection PyUnusedLocal
    @staticmethod
    def ws_url_cookie_name(request: HttpRequest) -> str:
        return "dfwsurl"

    # noinspection PyUnusedLocal
    @staticmethod
    def ws_windowkey_cookie_name(request: HttpRequest) -> str:
        return "dfwskey"

    def process_request(self, request: HttpRequest):
        request.window_key = None
        if request.is_ajax():
            request.window_key = request.META.get(
                "HTTP_%s" % self.ws_windowkey_header_name
            )
            name = self.ws_windowkey_cookie_name(request)
            if not request.window_key and name in request.COOKIES:
                request.window_key = request.COOKIES[name]
        if not request.window_key:
            request.window_key = get_random_string(32, VALID_KEY_CHARS)
        request.has_websocket_topics = False

    def process_response(self, request: HttpRequest, response: HttpResponse):
        # noinspection PyUnresolvedReferences
        if request.has_websocket_topics:
            # noinspection PyUnresolvedReferences
            window_key = request.window_key
            use_ssl = request.scheme.endswith("s")
            host = getattr(settings, "SERVER_NAME")
            port = getattr(settings, "SERVER_PORT")
            ws_url = ws_settings.WEBSOCKET_URL
            param = self.ws_windowkey_get_parameter
            if host and port:
                args = (
                    host,
                    port,
                    ws_url,
                    param,
                    window_key,
                )
                if use_ssl:
                    ws_url = "wss://%s:%s%s?%s=%s" % args
                else:
                    ws_url = "ws://%s:%s%s?%s=%s" % args
            else:
                http_url = request.build_absolute_uri(ws_url)
                ws_url = "ws%s?%s=%s" % (http_url[4:], param, window_key,)
            response.set_cookie(
                self.ws_url_cookie_name(request),
                quote_plus(ws_url),
                max_age=86400,
                domain=settings.CSRF_COOKIE_DOMAIN,
                path=settings.CSRF_COOKIE_PATH,
                secure=use_ssl,
                httponly=False,
                samesite=settings.CSRF_COOKIE_SAMESITE,
            )
            response.set_cookie(
                self.ws_windowkey_cookie_name(request),
                window_key,
                max_age=86400,
                domain=settings.CSRF_COOKIE_DOMAIN,
                path=settings.CSRF_COOKIE_PATH,
                secure=use_ssl,
                httponly=False,
                samesite=settings.CSRF_COOKIE_SAMESITE,
            )
        return response
