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

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

try:
    from django.core.handlers.asgi import ASGIHandler
except ImportError:  # django < 3.0
    ASGIHandler = None
from django.urls import path

from df_websockets import ws_settings
from df_websockets.consumers import DFConsumer

consumer = DFConsumer
if hasattr(DFConsumer, "as_asgi"):
    consumer = DFConsumer.as_asgi()
websocket_urlpatterns = [
    path(ws_settings.WEBSOCKET_URL[1:], consumer),
]

mapping = {
    "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
}
if ASGIHandler:
    mapping["http"] = ASGIHandler()
application = ProtocolTypeRouter(mapping)
