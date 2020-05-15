# ##############################################################################
#  This file is part of Interdiode                                             #
#                                                                              #
#  Copyright (C) 2020 Matthieu Gallet <matthieu.gallet@19pouces.net>           #
#  All Rights Reserved                                                         #
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
    ws_url_cookie_name = "dfwsurl"
    ws_windowkey_get_parameter = "dfwskey"
    ws_windowkey_cookie_name = "dfwskey"
    ws_windowkey_header_name = "DFWSKEY"

    def process_request(self, request: HttpRequest):
        request.window_key = None
        if request.is_ajax():
            request.window_key = request.META.get(
                "HTTP_%s" % self.ws_windowkey_header_name
            )
            if (
                not request.window_key
                and self.ws_windowkey_cookie_name in request.COOKIES
            ):
                request.window_key = request.COOKIES[self.ws_windowkey_cookie_name]
        if not request.window_key:
            request.window_key = get_random_string(32, VALID_KEY_CHARS)
        request.has_websocket_topics = False

    def process_response(self, request: HttpRequest, response: HttpResponse):
        # noinspection PyUnresolvedReferences
        if request.has_websocket_topics:
            http_url = request.build_absolute_uri(ws_settings.WEBSOCKET_URL)
            use_ssl = request.scheme.endswith("s")
            # noinspection PyUnresolvedReferences
            window_key = request.window_key
            ws_url = "ws%s?%s=%s" % (
                http_url[4:],
                self.ws_windowkey_get_parameter,
                window_key,
            )
            response.set_cookie(
                self.ws_url_cookie_name,
                quote_plus(ws_url),
                max_age=86400,
                domain=settings.CSRF_COOKIE_DOMAIN,
                path=settings.CSRF_COOKIE_PATH,
                secure=use_ssl,
                httponly=False,
                samesite=settings.CSRF_COOKIE_SAMESITE,
            )
            response.set_cookie(
                self.ws_windowkey_cookie_name,
                window_key,
                max_age=86400,
                domain=settings.CSRF_COOKIE_DOMAIN,
                path=settings.CSRF_COOKIE_PATH,
                secure=use_ssl,
                httponly=False,
                samesite=settings.CSRF_COOKIE_SAMESITE,
            )
        return response
