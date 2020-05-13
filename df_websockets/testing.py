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

from df_websockets import tasks as tasks_module

__author__ = "Matthieu Gallet"


class SignalQueue:
    """Allow to keep called signals in memory instead of actualling sending them to Redis, for testing purposes.

    >>> from df_websockets.tasks import trigger, SERVER
    >>> from df_websockets.window_info import WindowInfo
    >>> from df_websockets.topics import serialize_topic
    >>> from df_websockets.decorators import signal
    >>> # noinspection PyUnusedLocal
    >>> @signal(path='test.signal', queue='demo-queue')
    >>> def test_signal(window_info, value=None):
    ...     # noinspection PyUnresolvedReferences
    ...     print(value)
    >>>
    >>> wi = WindowInfo()
    >>> with SignalQueue() as fd:
    ...     trigger(wi, 'test.signal', to=[SERVER, 1], value="test value")
    >>> 'demo-queue' in fd.python_signals
    True
    >>> serialize_topic(wi, 1) in fd.ws_signals
    True
    >>> fd.ws_signals[serialize_topic(wi, 1)]
    ('test.signal', {'value': 'test value'})
    >>> fd.execute_delayed_signals()
    'test value'


    Of course, you should use this example from a method of a :class:`django.test.TestCase`.

    """

    def __init__(self, immediate_execution: bool = False):
        self.immediate = immediate_execution
        self.ws_signals = {}  # javascript_signals[client] = [signal1, signal2, …]
        self.python_signals = {}  # javascript_signals[queue] = [signal1, signal2, …]
        self._old_async_method = None
        self._old_ws_function = None

    def activate(self):
        """replace private function that push signal calls to Celery or Websockets """
        task_function = getattr(tasks_module, "_server_signal_call")
        encoder = getattr(tasks_module, "_signal_encoder")
        if self.immediate:
            # noinspection PyUnusedLocal
            def apply_async(signal_arguments, queue=None, **kwargs):
                json.dumps(
                    signal_arguments, cls=encoder
                )  # to check if args are JSON-serializable
                return task_function(*signal_arguments)

        else:
            # noinspection PyUnusedLocal
            def apply_async(signal_arguments, queue=None, **kwargs):
                json.dumps(
                    signal_arguments, cls=encoder
                )  # to check if args are JSON-serializable
                self.python_signals.setdefault(queue, []).append(signal_arguments)

        self._old_async_method = getattr(task_function, "apply_async")
        setattr(task_function, "apply_async", apply_async)

        # noinspection PyUnusedLocal
        def ws_signal_call(signal_name, signal_id, serialized_topic, kwargs):
            json.dumps(kwargs, cls=encoder)  # to check if args are JSON-serializable
            self.ws_signals.setdefault(serialized_topic, []).append(
                (signal_name, kwargs)
            )

        self._old_ws_function = getattr(tasks_module, "_call_ws_signal")
        setattr(tasks_module, "_call_ws_signal", ws_signal_call)

    def deactivate(self):
        """ replace the normal private functions for calling Celery or websockets signals"""
        task = getattr(tasks_module, "_server_signal_call")
        setattr(task, "apply_async", self._old_async_method)
        self._old_async_method = None
        setattr(tasks_module, "_call_ws_signal", self._old_ws_function)
        self._old_ws_function = None

    def execute_delayed_signals(self, queues=None):
        """ execute the Celery signals """
        task = getattr(tasks_module, "_server_signal_call")
        if queues is None:
            queues = self.python_signals.keys()
        for queue in queues:
            while queues[queue]:
                signal_arguments = self.python_signals[queue].pop()
                task(*signal_arguments)

    def __enter__(self):
        self.activate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deactivate()
