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

try:
    # noinspection PyPackageRequirements
    from celery import shared_task
except ImportError:
    shared_task = None

# noinspection PyUnresolvedReferences
from df_websockets.triggering import (
    BROADCAST,
    Constant,
    SERVER,
    SESSION,
    SYNC,
    USER,
    WINDOW,
    _call_ws_signal,
    _trigger_signal,
    get_expected_queues,
    get_websocket_redis_connection,
    import_signals_and_functions,
    process_task,
    redis_connection_pool,
    set_websocket_topics,
    trigger,
    trigger_signal,
)

if shared_task is not None:

    @shared_task(serializer="json", bind=True)
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
            kwargs=kwargs,
            from_client=from_client,
            serialized_client_topics=serialized_client_topics,
            to_server=to_server,
            queue=queue,
            celery_request=self.request,
        )
