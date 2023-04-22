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
import warnings

from django.conf import settings

from df_websockets import constants
from df_websockets.constants import RemovedInDfWebsockets2Warning

CELERY_APP = getattr(settings, "CELERY_APP", "df_websockets")


def compatibility_setting(new_name, old_name, default):
    if hasattr(settings, new_name):
        return getattr(settings, new_name)
    elif hasattr(settings, old_name):
        warnings.warn(
            f"{old_name} settings is replaced by {new_name}.",
            category=RemovedInDfWebsockets2Warning,
            stacklevel=2,
        )
        return getattr(settings, old_name)
    else:
        return default


WEBSOCKET_DEFAULT_QUEUE = compatibility_setting(
    "WEBSOCKET_DEFAULT_QUEUE", "CELERY_DEFAULT_QUEUE", "celery"
)
WEBSOCKET_CACHE_EXPIRE = compatibility_setting(
    "WEBSOCKET_CACHE_EXPIRE", "WEBSOCKET_REDIS_EXPIRE", 36000
)
WEBSOCKET_CACHE_PREFIX = compatibility_setting(
    "WEBSOCKET_CACHE_PREFIX", "WEBSOCKET_REDIS_PREFIX", "df_ws"
)
WEBSOCKET_CACHE_BACKEND = getattr(settings, "WEBSOCKET_CACHE_BACKEND", "default")
WEBSOCKET_SIGNAL_DECODER = getattr(
    settings, "WEBSOCKET_SIGNAL_DECODER", "json.JSONDecoder"
)
WEBSOCKET_SIGNAL_ENCODER = getattr(
    settings,
    "WEBSOCKET_SIGNAL_ENCODER",
    "django.core.serializers.json.DjangoJSONEncoder",
)
WEBSOCKET_TOPIC_SERIALIZER = getattr(
    settings, "WEBSOCKET_TOPIC_SERIALIZER", "df_websockets.topics.serialize_topic"
)
WEBSOCKET_WORKERS = getattr(settings, "WEBSOCKET_WORKERS", constants.WORKER_CELERY)
if WEBSOCKET_WORKERS == constants.WORKER_CELERY:
    try:
        import celery
    except ImportError:
        WEBSOCKET_WORKERS = constants.WORKER_THREAD
# "celery", "channels", "multithread", "multiprocess"
WEBSOCKET_POOL_SIZES = getattr(settings, "WEBSOCKET_POOL_SIZES", {None: 10})
WINDOW_INFO_MIDDLEWARES = getattr(
    settings,
    "WINDOW_INFO_MIDDLEWARES",
    [
        "df_websockets.ws_middleware.WindowKeyMiddleware",
        "df_websockets.ws_middleware.DjangoAuthMiddleware",
        "df_websockets.ws_middleware.Djangoi18nMiddleware",
        "df_websockets.ws_middleware.BrowserMiddleware",
    ],
)
WEBSOCKET_URL = getattr(settings, "WEBSOCKET_URL", "/ws/")
ASGI_APPLICATION = getattr(
    settings, "ASGI_APPLICATION", "df_websockets.routing.application"
)
settings.ASGI_APPLICATION = ASGI_APPLICATION
