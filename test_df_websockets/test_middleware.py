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
from urllib.parse import unquote

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.test import TestCase

from df_websockets import ws_settings
from df_websockets.constants import WEBSOCKET_KEY_COOKIE_NAME, WEBSOCKET_URL_COOKIE_NAME
from df_websockets.middleware import WebsocketMiddleware
from df_websockets.tasks import set_websocket_topics


class TestWebsocketMiddleware(TestCase):
    def test_websocketmiddleware_empty(self):
        request = HttpRequest()
        response = HttpResponse()
        cls = WebsocketMiddleware(lambda _: HttpResponse())
        req = cls.process_request(request)
        self.assertIsNone(req)
        # noinspection PyUnresolvedReferences
        self.assertFalse(request.has_websocket_topics)
        # noinspection PyUnresolvedReferences
        self.assertIsNotNone(request.window_key)
        cls.process_response(request, response)

    def test_websocketmiddleware(self):

        request = HttpRequest()
        with self.settings(ALLOWED_HOSTS=["example.com", "example.com:8000"]):
            request.META = {"SERVER_NAME": "example.com", "SERVER_PORT": "8000"}
            response = HttpResponse()
            cls = WebsocketMiddleware(lambda _: HttpResponse())
            req = cls.process_request(request)
            self.assertIsNone(req)
            # noinspection PyUnresolvedReferences
            self.assertFalse(request.has_websocket_topics)
            set_websocket_topics(request)
            # noinspection PyUnresolvedReferences
            self.assertTrue(request.has_websocket_topics)
            # noinspection PyUnresolvedReferences
            window_key = request.window_key
            self.assertIsNotNone(window_key)
            response_ = cls.process_response(request, response)
            window_key_ = response_.cookies[WEBSOCKET_KEY_COOKIE_NAME].value
            self.assertEqual(window_key, window_key_)
            ws_url = response_.cookies[WEBSOCKET_URL_COOKIE_NAME].value
            self.assertEqual(
                "ws://example.com:8000%s" % ws_settings.WEBSOCKET_URL, unquote(ws_url)
            )
