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
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.core.handlers.base import BaseHandler
from django.http import HttpRequest, HttpResponse, QueryDict
from django.utils.module_loading import import_string

from df_websockets import tasks, ws_settings
from df_websockets.constants import WEBSOCKET_KEY_COOKIE_NAME
from df_websockets.utils import valid_topic_name
from df_websockets.window_info import WindowInfo

logger = logging.getLogger("df_websockets.signals")
_signal_encoder = import_string(ws_settings.WEBSOCKET_SIGNAL_ENCODER)
topic_serializer = import_string(ws_settings.WEBSOCKET_TOPIC_SERIALIZER)
signal_decoder = import_string(ws_settings.WEBSOCKET_SIGNAL_DECODER)


def get_websocket_topics(request: Union[HttpRequest, WindowInfo]):
    if not hasattr(request, "window_key"):
        return []
    # noinspection PyUnresolvedReferences
    cache_key = "%s%s" % (
        ws_settings.WEBSOCKET_CACHE_PREFIX,
        request.window_key,
    )
    cache = caches[ws_settings.WEBSOCKET_CACHE_BACKEND]
    topic_string = cache.get(cache_key, "[]")
    logger.debug("websocket %s is bound to topics %s", cache_key, topic_string)
    return [valid_topic_name(x) for x in json.loads(topic_string)]


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
            request.window_key = request.COOKIES.get(WEBSOCKET_KEY_COOKIE_NAME, "")
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
        for header_name_bytes, header_value_bytes in self.scope.get("headers", []):
            header_name = header_name_bytes.decode("latin1").upper().replace("-", "_")
            if header_name not in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                header_name = "HTTP_%s" % header_name
            # HTTPbis say only ASCII chars are allowed in headers, but we latin1 just in case
            header_value = header_value_bytes.decode("latin1")
            if header_name in request.META:
                request.META[header_name] += "," + header_value
            else:
                request.META[header_name] = header_value
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
        request.META["wsgi.multithread"] = True
        request.META["wsgi.multiprocess"] = True
        request.COOKIES = self.scope.get("cookies", {})
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
            logger.debug('WS message received "%s"', text_data)
            if "signal" in msg:
                kwargs = msg["opts"]
                signal_name = msg["signal"]
                eta = int(msg.get("eta", 0)) or None
                expires = int(msg.get("expires", 0)) or None
                countdown = int(msg.get("countdown", 0)) or None
                # noinspection PyProtectedMember
                tasks._trigger_signal(
                    self.window_info,
                    signal_name,
                    to=[tasks.SERVER],
                    kwargs=kwargs,
                    from_client=True,
                    eta=eta,
                    expires=expires,
                    countdown=countdown,
                )
        except Exception as e:
            logger.exception(e)


class BackgroundConsumer(SyncConsumer):
    # noinspection PyMethodMayBeStatic
    def process_signal(
        self,
        data,
    ):
        (
            signal_name,
            window_info_dict,
            kwargs,
            from_client,
            serialized_client_topics,
            to_server,
            queue,
        ) = data["args"]
        tasks.process_task(
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
