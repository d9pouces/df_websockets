"""WindowInfo object and associated functions
==========================================

A :class:`WindowInfo` object carries important data the browser window that is connected to the websocket:

  * the window key that is unique to each open browser window,
  * user information about the connected user,
  * i18n information.

The :class:`WindowInfo` object is populated by middlewares, thath should be any subclass of
:class:`df_websockets.ws_middleware.WindowInfoMiddleware`.
The list of used middlewares is defined by the `WINDOW_INFO_MIDDLEWARES` setting.

.. warning::
  Never modify a :class:`WindowInfo`: the same object can be reused for all websocket signals from a given connection.

Designed to be instanciated from a :class:`django.http.request.HttpRequest` and reused across signals
(when a signal calls another one). However, a blank :class:`WindowInfo` can also be directly instanciated.

"""
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

import logging

from django.conf import settings
from django.template.loader import render_to_string as raw_render_to_string
from django.utils.module_loading import import_string

__author__ = "Matthieu Gallet"

from df_websockets import ws_settings

logger = logging.getLogger("df_websockets.signals")
middlewares = [import_string(x)() for x in ws_settings.WINDOW_INFO_MIDDLEWARES]


class Session:
    def __init__(self, key=None):
        self.key = key


class WindowInfo:
    """ Built to store the username and the window key and must be supplied to any Python signal call.
    All attributes are set by "WindowInfoMiddleware"'s.

    Can be constructed from a standard :class:`django.http.HttpRequest` or from a dict.
    Like the request, you should check the installed middlewares to obtain the full list of attributes.
    The default ones are provided by :mod:`df_websockets.middleware`.
    """

    def __init__(self, init=True):
        if init:
            for mdw in middlewares:
                mdw.new_window_info(self)

    @classmethod
    def from_dict(cls, values):
        """Generate a new :class:`WindowInfo` from a dict."""
        if values is None:
            return None
        window_info = cls(init=False)
        for mdw in middlewares:
            mdw.from_dict(window_info, values=values)
        return window_info

    def to_dict(self):
        """Convert this :class:`df_websockets.window_info.WindowInfo` to a :class:`dict` which can be provided to JSON.

        :return: a dict ready to be serialized in JSON
        :rtype: :class:`dict`
        """
        result = {}
        for mdw in middlewares:
            extra_values = mdw.to_dict(self)
            if extra_values:
                result.update(extra_values)
        return result

    @classmethod
    def from_request(cls, request):
        """ return a :class:`df_websockets.window_info.WindowInfo` from a :class:`django.http.HttpRequest`.

        If the request already is a :class:`df_websockets.window_info.WindowInfo`,
        then it is returned as-is (not copied!).

        :param request: standard Django request
        :type request: :class:`django.http.HttpRequest` or :class:`df_websockets.window_info.WindowInfo`
        :return: a valid request
        :rtype: :class:`df_websockets.window_info.WindowInfo`
        """
        if isinstance(request, WindowInfo):
            return request
        elif request is None:
            return WindowInfo()
        window_info = cls(init=False)
        for mdw in middlewares:
            mdw.from_request(request, window_info)
        return window_info


for mdw_ in middlewares:
    mdw_.install_methods(WindowInfo)


def get_window_context(window_info):
    """Generate a template context from the `window_info`, equivalent of a template
    context from a :class:`django.http.request.HttpRequest`."""
    context = {}
    if window_info:
        for mdw in middlewares:
            context.update(mdw.get_context(window_info))
    return context


def render_to_string(template_name, context=None, window_info=None, using=None):
    """Render a template to a string using a context from the `window_info`, equivalent of
the :meth:`django.template.loader.render_to_string`."""
    if window_info is not None and context:
        window_context = get_window_context(window_info)
        window_context.update(context)
    elif window_info is not None:
        window_context = get_window_context(window_info)
    else:
        window_context = context
    return raw_render_to_string(
        template_name, context=window_context or {}, using=using
    )
