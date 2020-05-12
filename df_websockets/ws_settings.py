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

for name, default in (
        ("CELERY_APP", "df_websockets"),
        ("CELERY_DEFAULT_QUEUE", "celery"),
        ("WEBSOCKET_REDIS_CONNECTION", {'host': 'localhost', 'port': 6379, 'db': 3, 'password': ''}),
        ("WEBSOCKET_REDIS_EXPIRE", 36000),
        ("WEBSOCKET_REDIS_PREFIX", "ws"),
        ("WEBSOCKET_SIGNAL_DECODER", "json.JSONDecoder"),
        ("WEBSOCKET_SIGNAL_ENCODER", "django.core.serializers.json.DjangoJSONEncoder"),
        ("WEBSOCKET_TOPIC_SERIALIZER", "df_websockets.topics.serialize_topic"),
        ("WINDOW_INFO_MIDDLEWARES", [
            "df_websockets.ws_middleware.WindowKeyMiddleware",
            "df_websockets.ws_middleware.DjangoAuthMiddleware",
            "df_websockets.ws_middleware.Djangoi18nMiddleware",
            "df_websockets.ws_middleware.BrowserMiddleware",
        ]),
        ("WEBSOCKET_URL", "/ws/"),
        ("ASGI_APPLICATION", "df_websockets.routing.application"),
):
    pass
