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
from django.contrib.auth import get_user_model
from django.db.models import Model

from df_websockets.window_info import Session


def serialize_topic(window_info, obj):
    """ The default serialization function can serialize any Python object with the following rules

  * :class:`df_websockets.tasks.BROADCAST` to '-broadcast'
  * :class:`df_websockets.tasks.WINDOW` to '-window.' + the unique window key provided
    by the :class:`df_websockets.window_info.WindowInfo` object,
  * :class:`django.db.models.Model` as "app_label.model_name.primary_key"
  * :class:`df_websockets.tasks.USER` to converted to the authenticated user then
    serialized as any Django model,
  * :class:`django.wsgi.window_info.Session` serialized to "-session.key"
  * other objects are serialized to "class.hash(obj)"

"""
    from df_websockets.tasks import BROADCAST, USER, WINDOW

    if obj is BROADCAST:
        return "-broadcast"
    elif obj is WINDOW:
        if window_info is None:
            return None
        return "-window.%s" % window_info.window_key
    elif isinstance(obj, type):
        return "-<%s>" % obj.__name__
    elif isinstance(obj, Model):
        # noinspection PyProtectedMember
        meta = obj._meta
        return "-%s.%s.%s" % (meta.app_label, meta.model_name, obj.pk or 0)
    elif obj is USER:
        if window_info is None:
            return None
        # noinspection PyProtectedMember
        meta = get_user_model()._meta
        return "-%s.%s.%s" % (meta.app_label, meta.model_name, window_info.user_pk)
    elif isinstance(obj, Session):
        return "-session.%s" % obj.key
    return "-%s.%s" % (obj.__class__.__name__, hash(obj))
