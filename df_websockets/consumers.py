# ##############################################################################
#  This file is part of Interdiode                                             #
#                                                                              #
#  Copyright (C) 2020 Matthieu Gallet <matthieu.gallet@19pouces.net>           #
#  All Rights Reserved                                                         #
#                                                                              #
# ##############################################################################
import json
import logging
from functools import lru_cache
from typing import Optional, Union

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from df_websockets import ws_settings
from df_websockets.middleware import WebsocketMiddleware
from df_websockets.tasks import SERVER, _trigger_signal, get_websocket_redis_connection
from df_websockets.utils import valid_topic_name
from df_websockets.window_info import WindowInfo
from django import http
from django.core.handlers.base import BaseHandler
from django.http import HttpRequest, HttpResponse, QueryDict
from django.utils.module_loading import import_string

logger = logging.getLogger("df_websockets.signals")
_signal_encoder = import_string(ws_settings.WEBSOCKET_SIGNAL_ENCODER)
topic_serializer = import_string(ws_settings.WEBSOCKET_TOPIC_SERIALIZER)
signal_decoder = import_string(ws_settings.WEBSOCKET_SIGNAL_DECODER)


def get_websocket_topics(request: Union[HttpRequest, WindowInfo]):
    # noinspection PyUnresolvedReferences
    redis_key = "%s%s" % (ws_settings.WEBSOCKET_REDIS_PREFIX, request.window_key)
    connection = get_websocket_redis_connection()
    topics = connection.lrange(redis_key, 0, -1)
    return [valid_topic_name(x) for x in topics]


class WebsocketHandler(BaseHandler):
    def _get_response(self, request):
        return HttpResponse(status=200)


@lru_cache()
def get_handler():
    handler = WebsocketHandler()
    handler.load_middleware()
    return handler


class DFConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window_info = None  # type: Optional[WindowInfo]
        self.topics = []

    def connect(self):
        request = self.build_http_request()
        handler = get_handler()
        handler.get_response(request)
        request.window_key = request.GET.get(
            WebsocketMiddleware.ws_windowkey_get_parameter, ""
        )
        self.topics = get_websocket_topics(request)
        self.window_info = WindowInfo.from_request(request)
        for topic in self.topics:
            async_to_sync(self.channel_layer.group_add)(topic, self.channel_name)
        super().connect()

    def build_http_request(self):
        request = HttpRequest()
        query_string = self.scope.get("query_string", "")
        if isinstance(query_string, bytes):
            query_string = query_string.decode("utf-8")
        request.method = "GET"
        request.path_info = self.scope["path"]
        request.GET = QueryDict(query_string=query_string)
        for name, value in self.scope.get("headers", []):
            name = name.decode("latin1")
            if name == "content-length":
                corrected_name = "CONTENT_LENGTH"
            elif name == "content-type":
                corrected_name = "CONTENT_TYPE"
            else:
                corrected_name = "HTTP_%s" % name.upper().replace("-", "_")
            # HTTPbis say only ASCII chars are allowed in headers, but we latin1 just in case
            value = value.decode("latin1")
            if corrected_name in request.META:
                value = request.META[corrected_name] + "," + value
            request.META[corrected_name] = value
        if self.scope.get("client", None):
            request.META["REMOTE_ADDR"] = self.scope["client"][0]
            request.META["REMOTE_HOST"] = request.META["REMOTE_ADDR"]
            request.META["REMOTE_PORT"] = self.scope["client"][1]
        if self.scope.get("server", None):
            request.META["SERVER_NAME"] = self.scope["server"][0]
            request.META["SERVER_PORT"] = str(self.scope["server"][1])
        else:
            request.META["SERVER_NAME"] = "unknown"
            request.META["SERVER_PORT"] = "0"
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
        request.COOKIES = http.parse_cookie(request.META.get("HTTP_COOKIE", ""))
        return request

    def disconnect(self, close_code):
        for topic in self.topics:
            async_to_sync(self.channel_layer.group_discard)(topic, self.channel_name)

    # Receive message from room group
    def ws_message(self, event):
        message = event["message"]
        self.send(text_data=message)

    # Receive message from WebSocket
    def receive(self, text_data=None, bytes_data=None):
        try:
            msg = json.loads(text_data)
            logger.debug('WS message received "%s"' % text_data)
            if "signal" in msg:
                kwargs = msg["opts"]
                signal_name = msg["signal"]
                eta = int(msg.get("eta", 0)) or None
                expires = int(msg.get("expires", 0)) or None
                countdown = int(msg.get("countdown", 0)) or None
                _trigger_signal(
                    self.window_info,
                    signal_name,
                    to=[SERVER],
                    kwargs=kwargs,
                    from_client=True,
                    eta=eta,
                    expires=expires,
                    countdown=countdown,
                )
        except Exception as e:
            logger.exception(e)
