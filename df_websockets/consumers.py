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
import json
import logging
from functools import lru_cache
from typing import Optional, Union

from asgiref.compatibility import guarantee_single_callable
from asgiref.sync import async_to_sync
from channels.consumer import SyncConsumer
from channels.generic.websocket import WebsocketConsumer
from channels.routing import ChannelNameRouter
from django import http
from django.core.exceptions import ImproperlyConfigured
from django.core.handlers.base import BaseHandler
from django.http import HttpRequest, HttpResponse, QueryDict
from django.utils.module_loading import import_string

from df_websockets import ws_settings, tasks
from df_websockets.middleware import WebsocketMiddleware
from df_websockets.tasks import SERVER, _trigger_signal, process_task
from df_websockets.utils import valid_topic_name
from df_websockets.window_info import WindowInfo

logger = logging.getLogger("df_websockets.signals")
_signal_encoder = import_string(ws_settings.WEBSOCKET_SIGNAL_ENCODER)
topic_serializer = import_string(ws_settings.WEBSOCKET_TOPIC_SERIALIZER)
signal_decoder = import_string(ws_settings.WEBSOCKET_SIGNAL_DECODER)


def get_websocket_topics(request: Union[HttpRequest, WindowInfo]):
    # noinspection PyUnresolvedReferences
    redis_key = "%s%s" % (
        ws_settings.WEBSOCKET_REDIS_PREFIX,
        getattr(request, "window_key", ""),
    )
    connection = tasks.get_websocket_redis_connection()
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
        try:
            request = self.build_http_request()
            handler = get_handler()
            handler.get_response(request)
            request.window_key = request.GET.get(
                WebsocketMiddleware.ws_windowkey_get_parameter, ""
            )
            self.topics = get_websocket_topics(request)
            self.window_info = WindowInfo.from_request(request)
            if self.channel_layer:
                for topic in self.topics:
                    async_to_sync(self.channel_layer.group_add)(
                        topic, self.channel_name
                    )
            else:
                raise ImproperlyConfigured(
                    "a channel layer must be installed and configured first."
                )
            super().connect()
        except Exception as e:
            logger.exception(e)
            raise e

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


class BackgroundConsumer(SyncConsumer):
    def process_signal(
        self,
            data,
    ):
        signal_name, window_info_dict, kwargs,  from_client , serialized_client_topics, to_server, queue = data["args"]
        # 'type': 'process.signal', 'args': ['df_websockets_demo.check_csp', {'window_key': 'go073jwd433yzmfa2lfq13zwjcpewr8x', 'user_pk': None, 'username': None, 'is_superuser': False, 'is_staff': False, 'is_active': False, 'csrf_cookie': 'MZSbRdm6EbMwvRyexRr9ZQiltfaEk40Rj1L7kbjX4IMsbpFDe51Rai0sSFnhD5dK', 'perms': None, 'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15', 'user_set': False, 'language_code': 'fr'}, {'form_data': [{'name': 'url', 'value': 'https://aviationsmilitaires.net/v3/tracking/sujets%20non%20lus%20/'}]}, True, [], True, 'celery']},
        process_task(
            signal_name,
            window_info_dict,
            kwargs=kwargs,
            from_client=from_client,
            serialized_client_topics=serialized_client_topics,
            to_server=to_server,
            queue=queue,
            celery_request=None,
        )


class DFChannelNameRouter(ChannelNameRouter):
    def __init__(self):
        super().__init__({})
        self.application = BackgroundConsumer.as_asgi()

    async def __call__(self, scope, receive, send):
        if "channel" not in scope:
            raise ValueError(
                "ChannelNameRouter got a scope without a 'channel' key. "
                + "Did you make sure it's only being used for 'channel' type messages?"
            )
        application = guarantee_single_callable(self.application)
        return await application(scope, receive, send)
