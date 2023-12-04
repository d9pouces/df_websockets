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

"""Define Celery tasks and functions for calling signals
=====================================================

This module is automatically imported by Celery.
Use these functions for:

  * setting websocket channels allowed for a given :class:`django.http.response.HttpResponse`,
  * calling signals, with a full function (:meth:`df_websockets.tasks.call`) and a
    shortcut (:meth:`df_websockets.tasks.trigger`)

"""

import json
import logging
import multiprocessing.pool
import os
import uuid
from functools import lru_cache
from importlib import import_module
from typing import Dict, List

import django
from asgiref.sync import async_to_sync
from django.core.cache import caches

try:
    from celery import shared_task as celery_shared_task
except ImportError:
    celery_shared_task = None

from channels import DEFAULT_CHANNEL_LAYER
from channels.layers import get_channel_layer
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from df_websockets import ws_settings
from df_websockets.constants import (
    WORKER_CELERY,
    WORKER_CHANNEL,
    WORKER_PROCESS,
    WORKER_THREAD,
)
from df_websockets.decorators import (
    REGISTERED_SIGNALS,
    DynamicQueueName,
    SignalConnection,
)
from df_websockets.utils import valid_topic_name
from df_websockets.window_info import WindowInfo, middlewares

logger = logging.getLogger("df_websockets.signals")
_PROCESS_POOLS = {}  # type: Dict[str, multiprocessing.pool.Pool]


class Constant:
    """Allow to define constants that can be nicely printed to stdout"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


# special values for the "to" argument
SERVER = Constant("SERVER")
SESSION = Constant("SESSION")
WINDOW = Constant("WINDOW")
USER = Constant("USER")
BROADCAST = Constant("BROADCAST")
# special value for the "queue" argument
SYNC = Constant("SYNC")

_signal_encoder = import_string(ws_settings.WEBSOCKET_SIGNAL_ENCODER)
_topic_serializer = import_string(ws_settings.WEBSOCKET_TOPIC_SERIALIZER)


def set_websocket_topics(request, *topics):
    """Use it in a Django view for setting websocket topics. Any signal sent to one of these topics will be received
    by the client.

        :param request: :class:`django.http.request.HttpRequest`
        :param topics: list of topics that will be subscribed by the websocket (can be any Python object).
    """
    # noinspection PyTypeChecker
    if not hasattr(request, "window_key"):
        raise ImproperlyConfigured("WebsocketMiddleware middleware is required.")
    request.has_websocket_topics = True
    request = WindowInfo.from_request(request)
    topic_strings = {_topic_serializer(request, x) for x in topics if x is not SERVER}
    # noinspection PyUnresolvedReferences,PyTypeChecker
    if getattr(request, "user", None) and request.user.is_authenticated:
        topic_strings.add(_topic_serializer(request, USER))
    topic_strings.add(_topic_serializer(request, WINDOW))
    topic_strings.add(_topic_serializer(request, BROADCAST))
    topic_string = json.dumps(list(topic_strings))
    # noinspection PyUnresolvedReferences
    cache_key = "%s%s" % (ws_settings.WEBSOCKET_CACHE_PREFIX, request.window_key)
    cache = caches[ws_settings.WEBSOCKET_CACHE_BACKEND]
    cache.set(cache_key, topic_string, ws_settings.WEBSOCKET_CACHE_EXPIRE)
    logger.debug("websocket %s is now bound to topics %s", cache_key, topic_string)


def trigger(window_info, signal_name, to=None, **kwargs):
    """Shortcut to :meth:`df_websockets.tasks.call`, allowing to directly pass arguments of the signal to this function.
    Your signal cannot use `window_info`, `signal_name` and `to` as argument names.

    These two successive calls are strictly equivalent:

    .. code-block:: python

        from df_websockets.tasks import call, trigger, WINDOW, SERVER

        def my_python_view(request):
            trigger(request, 'my.signal.name', to=[WINDOW, SERVER], arg1=12, arg2='Hello')
            trigger_signal(request, 'my.signal.name', to=[WINDOW, SERVER], kwargs={'arg1': 12, 'arg2': 'Hello'})

    """
    return _trigger_signal(
        window_info, signal_name, to=to, kwargs=kwargs, from_client=False
    )


# noinspection PyIncorrectDocstring
def trigger_signal(
    window_info,
    signal_name,
    to=None,
    kwargs=None,
    countdown=None,
    expires=None,
    eta=None,
):
    """Call a df_websockets signal.

    :param window_info: either a :class:`django.http.request.HttpRequest` or
        a :class:`df_websockets.window_info.WindowInfo`
    :param signal_name: name of the called signal (:class:`str`)
    :param to: :class:`list` of the topics that should receive the signal
    :param kwargs: dict with all arguments of your signal. Will be encoded to JSON with
       `settings.WEBSOCKET_SIGNAL_ENCODER` and decoded with `settings.WEBSOCKET_SIGNAL_DECODER`.
    :param countdown: check the Celery doc (in a nutshell: number of seconds before executing the signal)
    :param expires: check the Celery doc (in a nutshell: if this signal is not executed before this number of seconds,
       it is cancelled)
    :param eta: check the Celery doc (in a nutshell: datetime of running this signal)
    """
    return _trigger_signal(
        window_info,
        signal_name,
        to=to,
        kwargs=kwargs,
        countdown=countdown,
        expires=expires,
        eta=eta,
        from_client=False,
    )


def _trigger_signal(
    window_info,
    signal_name,
    to=None,
    kwargs=None,
    countdown=None,
    expires=None,
    eta=None,
    from_client=False,
):
    return async_to_sync(_trigger_signal_async)(
        window_info,
        signal_name,
        to=to,
        kwargs=kwargs,
        countdown=countdown,
        expires=expires,
        eta=eta,
        from_client=from_client,
    )


async def _trigger_signal_async(
    window_info,
    signal_name,
    to=None,
    kwargs=None,
    countdown=None,
    expires=None,
    eta=None,
    from_client=False,
):
    """actually calls a DF signal, dispatching them to their destination:

    * only calls Celery tasks if a delay is required (`coutdown` argument)
    * write messages to websockets if no delay is required

    """
    import_signals_and_functions()
    window_info = WindowInfo.from_request(
        window_info
    )  # ensure that we always have a true WindowInfo object
    if kwargs is None:
        kwargs = {}
    for k in (SERVER, WINDOW, USER, BROADCAST):
        if to is k:
            to = [k]
    if to is None:
        to = [USER]
    window_info_as_dict = None
    if window_info:
        window_info_as_dict = window_info.to_dict()

    serialized_client_topics = []
    to_server = False
    to_sync = False
    logger.debug('received signal "%s" to %r', signal_name, to)
    for topic in to:
        if topic is SERVER:
            if signal_name not in REGISTERED_SIGNALS:
                logger.debug('Signal "%s" is unknown by the server.', signal_name)
            to_server = True
        elif topic is SYNC:
            if signal_name not in REGISTERED_SIGNALS:
                logger.debug('Signal "%s" is unknown by the server.', signal_name)
            to_sync = True
        else:
            serialized_topic = _topic_serializer(window_info, topic)
            if serialized_topic is not None:
                serialized_client_topics.append(serialized_topic)
    celery_options = {}
    if expires:
        celery_options["expires"] = expires
    if eta:
        celery_options["eta"] = eta
    if countdown:
        celery_options["countdown"] = countdown
    worker_mode = ws_settings.WEBSOCKET_WORKERS
    if celery_options and worker_mode != WORKER_CELERY:
        raise ValueError(
            "Unable to use eta, countdown or expires in signals when not using Celery."
        )
    queues = {
        x.get_queue(window_info, kwargs)
        for x in REGISTERED_SIGNALS.get(signal_name, [])
    }

    if celery_options and serialized_client_topics:
        # we do not send to WS clients now (countdown or eta)
        background_client_topics = serialized_client_topics
        queues.add(ws_settings.WEBSOCKET_DEFAULT_QUEUE)
        to_server = True
    else:
        background_client_topics = []
    if to_sync:
        for queue in queues:
            process_task(
                signal_name,
                window_info_as_dict,
                kwargs=kwargs,
                from_client=from_client,
                to_server=True,
                queue=queue,
            )

    if to_server:
        for queue in queues:
            topics = (
                background_client_topics
                if queue == ws_settings.WEBSOCKET_DEFAULT_QUEUE
                else []
            )
            celery_args = [
                signal_name,
                window_info_as_dict,
                kwargs,
                from_client,
                topics,
                to_server,
                queue,
            ]
            call_task(worker_mode, queue, celery_args, celery_options)
    if serialized_client_topics and not celery_options:
        signal_id = str(uuid.uuid4())
        await _call_ws_signal(signal_name, signal_id, serialized_client_topics, kwargs)


def call_task(worker_mode, queue, signal_args, celery_options):
    if worker_mode == WORKER_CELERY:
        logger.debug("Call Celery task to queue %s.", queue)
        _server_signal_call.apply_async(
            args=signal_args, queue=queue, add_to_parent=False, **celery_options
        )
    elif worker_mode == WORKER_CHANNEL:
        logger.debug("Call Channels task to queue %s.", queue)
        channel_layer = get_channel_layer(DEFAULT_CHANNEL_LAYER)
        async_to_sync(channel_layer.send)(
            queue,
            {"type": "process.signal", "args": signal_args},
        )
    elif worker_mode in {WORKER_THREAD, WORKER_PROCESS}:
        if queue not in _PROCESS_POOLS:
            pool_size = ws_settings.WEBSOCKET_POOL_SIZES.get(
                queue, ws_settings.WEBSOCKET_POOL_SIZES.get(None, 5)
            )
            if ws_settings.WEBSOCKET_WORKERS == WORKER_THREAD:
                logger.debug("Call thread task to queue %s.", queue)
                pool = multiprocessing.pool.ThreadPool(pool_size)
            else:
                logger.debug("Call multiprocess task to queue %s.", queue)
                pool = multiprocessing.pool.Pool(
                    pool_size, initializer=django.setup, initargs=()
                )
            _PROCESS_POOLS[queue] = pool
        pool = _PROCESS_POOLS[queue]  # type: multiprocessing.pool.Pool
        pool.apply_async(process_task, args=signal_args)
    else:
        raise ImproperlyConfigured(
            "Invalid WEBSOCKET_WORKERS settings: %s" % worker_mode
        )


def process_task(
    signal_name,
    window_info_dict,
    kwargs=None,
    from_client=False,
    serialized_client_topics=None,
    to_server=False,
    queue=None,
    celery_request=None,
):
    logger.info(
        'Signal "%s" called on queue "%s" to topics %s (from client?: %s, to server?: %s)',
        signal_name,
        queue,
        serialized_client_topics,
        from_client,
        to_server,
    )
    try:
        if kwargs is None:
            kwargs = {}
        if serialized_client_topics:
            signal_id = str(uuid.uuid4())
            _call_ws_signal(signal_name, signal_id, serialized_client_topics, kwargs)
        window_info = WindowInfo.from_dict(window_info_dict)
        import_signals_and_functions()
        for mdw in middlewares:
            mdw.before_process(window_info)
        if celery_request is not None:
            window_info.celery_request = celery_request
        if not to_server or signal_name not in REGISTERED_SIGNALS:
            return
        for connection in REGISTERED_SIGNALS[signal_name]:
            assert isinstance(connection, SignalConnection)
            if connection.get_queue(window_info, kwargs) != queue or (
                from_client
                and not connection.is_allowed_to(connection, window_info, kwargs)
            ):
                continue
            new_kwargs = connection.check(kwargs)
            if new_kwargs is None:
                continue
            connection(window_info, **new_kwargs)
    except Exception as e:
        logger.exception(e)


async def _call_ws_signal(
    signal_name: str, signal_id, serialized_topics: List[str], kwargs
):
    if isinstance(serialized_topics, str):
        serialized_topics = [serialized_topics]
    serialized_message = json.dumps(
        {"signal": signal_name, "opts": kwargs, "signal_id": signal_id},
        cls=_signal_encoder,
    )
    channel_layer = get_channel_layer(DEFAULT_CHANNEL_LAYER)
    for serialized_topic in serialized_topics:
        logger.debug("send message to topic %r", serialized_topic)
        topic_valid = valid_topic_name(serialized_topic)
        # noinspection PyTypeChecker
        await channel_layer.group_send(
            topic_valid,
            {"type": "ws_message", "message": serialized_message},
        )


@lru_cache()
def import_signals_and_functions():
    """Import all `signals.py`, 'forms.py' and `functions.py` files to register signals and WS functions
    (tries these files for all Django apps).
    """

    def try_import(module):
        try:
            import_module(module)
        except ImportError as e:
            if package_dir and os.path.isfile(
                os.path.join(package_dir, "%s.py" % module_name)
            ):
                logger.exception(e)
        except Exception as e:
            logger.exception(e)

    if ws_settings.WEBSOCKET_WORKERS == WORKER_CELERY:
        # noinspection PyUnresolvedReferences
        import df_websockets.celery
    for app_config in apps.app_configs.values():
        app = app_config.name
        package_dir = app_config.path
        for module_name in (
            "signals",
            "forms",
        ):
            if os.path.isfile(os.path.join(package_dir, "%s.py" % module_name)):
                try_import("%s.%s" % (app, module_name))
            elif os.path.isdir(os.path.join(package_dir, module_name)):
                for f in os.listdir(os.path.join(package_dir, module_name)):
                    f = os.path.splitext(f)[0]
                    try_import("%s.%s.%s" % (app, module_name, f))
    logger.debug(
        "Found signals: %s",
        ", ".join(["%s (%d)" % (k, len(v)) for (k, v) in REGISTERED_SIGNALS.items()]),
    )


def get_expected_queues():
    expected_queues = set()
    import_signals_and_functions()
    for connections in REGISTERED_SIGNALS.values():
        for connection in connections:
            if isinstance(connection.queue, DynamicQueueName):
                for queue_name in connection.queue.get_available_queues():
                    expected_queues.add(queue_name)
            elif not callable(connection.queue):
                expected_queues.add(connection.queue)
    return expected_queues


if celery_shared_task is not None:

    @celery_shared_task(serializer="json", bind=True)
    def _server_signal_call(
        self,
        signal_name,
        window_info_dict,
        kwargs=None,
        from_client=False,
        serialized_client_topics=None,
        to_server=False,
        queue=None,
    ):
        return process_task(
            signal_name,
            window_info_dict,
            kwargs,
            from_client,
            serialized_client_topics,
            to_server,
            queue,
            self.request,
        )
