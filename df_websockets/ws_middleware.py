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
from django.contrib.auth import get_user_model
from django.contrib.auth.context_processors import PermWrapper
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import DEFAULT_LEVELS
from django.db.models import Q
from django.http import HttpRequest
from django.utils import translation
from django.utils.translation import get_language_from_request

logger = logging.getLogger("df_websockets.signals")


class WindowInfoMiddleware:
    """Base class for the WindowInfo middlewares."""

    def from_request(self, request, window_info):
        pass

    def new_window_info(self, window_info):
        pass

    def to_dict(self, window_info):
        return {}

    def from_dict(self, window_info, values):
        pass

    def get_context(self, window_info):
        return {}

    def install_methods(self, window_info_cls):
        pass


class WindowKeyMiddleware(WindowInfoMiddleware):
    """handle the unique ID generated for each :class:`django.http.request.HttpRequest` and copy
    it to the :class:`WindowInfo` object"""

    def from_request(self, request, window_info):
        # noinspection PyTypeChecker
        window_info.window_key = getattr(request, "window_key", None)

    def new_window_info(self, window_info):
        window_info.window_key = None

    def to_dict(self, window_info):
        return {"window_key": window_info.window_key}

    def from_dict(self, window_info, values):
        window_info.window_key = values.get("window_key")

    def get_context(self, window_info):
        # noinspection PyTypeChecker
        return {"df_window_key": getattr(window_info, "window_key")}


class DjangoAuthMiddleware(WindowInfoMiddleware):
    """handle attributes related to the :mod:`django.contrib.auth` framework"""

    def from_request(self, request, window_info):
        self.new_window_info(window_info)
        assert isinstance(request, HttpRequest)
        # auth and perms part
        # noinspection PyTypeChecker
        user = getattr(request, "user", None)
        window_info._user = user
        window_info._perms = None
        window_info._template_perms = None
        window_info.user_agent = request.META.get("HTTP_USER_AGENT", "")
        window_info.csrf_cookie = request.COOKIES.get("csrftoken", "")
        if user and user.is_authenticated:
            window_info.user_pk = user.pk
            window_info.username = user.get_username()
            window_info.is_superuser = user.is_superuser
            window_info.is_staff = user.is_staff
            window_info.is_active = user.is_active
            window_info.user_set = True
        else:
            window_info.user_pk = None
            window_info.username = None
            window_info.is_superuser = False
            window_info.is_staff = False
            window_info.is_active = False
            window_info.user_set = False

    def new_window_info(self, window_info):
        window_info._user = None
        window_info._perms = None
        window_info._template_perms = None
        window_info.user_agent = ""
        window_info.user_pk = None
        window_info.username = None
        window_info.is_superuser = False
        window_info.is_staff = False
        window_info.user_set = False
        window_info.is_active = False
        window_info.csrf_cookie = ""

    def to_dict(self, window_info):
        # noinspection PyProtectedMember
        return {
            "user_pk": window_info.user_pk,
            "username": window_info.username,
            "is_superuser": window_info.is_superuser,
            "is_staff": window_info.is_staff,
            "is_active": window_info.is_active,
            "csrf_cookie": window_info.csrf_cookie,
            "perms": list(window_info._perms)
            if isinstance(window_info._perms, set)
            else None,
            "user_agent": window_info.user_agent,
            "user_set": window_info.user_set,
        }

    def from_dict(self, window_info, values):
        window_info._user = None
        window_info.csrf_cookie = values.get("csrf_cookie")
        window_info.user_pk = values.get("user_pk")
        window_info.user_set = values.get("user_set")
        if window_info.user_pk and not window_info.user_set:
            user = get_user_model().objects.filter(pk=window_info.user_pk).first()
            window_info.username = user.username
            window_info.is_superuser = user.is_superuser
            window_info.is_staff = user.is_staff
            window_info.is_active = user.is_active
        else:
            window_info.username = values.get("username")
            window_info.is_superuser = values.get("is_superuser")
            window_info.is_staff = values.get("is_staff")
            window_info.is_active = values.get("is_active")
        window_info.is_authenticated = bool(window_info.user_pk)
        window_info.is_anonymous = not bool(window_info.user_pk)
        window_info._perms = (
            set(values["perms"]) if values.get("perms") is not None else None
        )
        window_info._template_perms = None
        window_info.user_agent = values.get("user_agent")

    def get_context(self, window_info):
        """provide the same context data as the :mod:`django.contrib.auth.context_processors`:

         * `user`: a user or :class:`django.contrib.auth.models.AnonymousUser`
         * `perms`, with the same meaning
        """
        user = window_info.user or AnonymousUser()
        return {
            "user": user,
            "perms": PermWrapper(user),
            "csrf_token": window_info.csrf_cookie,
        }

    def install_methods(self, window_info_cls):
        def get_user(req):
            """return the user object if authenticated, else return `None`"""
            # noinspection PyProtectedMember
            if req._user or req.user_pk is None:
                # noinspection PyProtectedMember
                return req._user
            user = get_user_model().objects.filter(pk=req.user_pk).first()
            if user:
                req._user = user
                return req._user
            return None

        def has_perm(req, perm):
            """ return true is the user has the required perm.

            >>> from df_websockets.window_info import WindowInfo
            >>> r = WindowInfo.from_dict({'username': 'username', 'perms':['app_label.codename']})
            >>> r.has_perm('app_label.codename')
            True

            :param req: WindowInfo
            :param perm: name of the permission  ("app_label.codename")
            :return: True if the user has the required perm
            :rtype: :class:`bool`
            """
            return perm in req.perms

        def get_perms(req):
            """:class:`set` of all perms of the user (set of "app_label.codename")"""
            if not req.user_pk:
                return set()
            elif req._perms is not None:
                return req._perms
            from django.contrib.auth.models import Permission

            if req.is_superuser:
                query = Permission.objects.all()
            else:
                query = Permission.objects.filter(
                    Q(user__pk=req.user_pk) | Q(group__user__pk=req.user_pk)
                )
            req._perms = set(
                "%s.%s" % p
                for p in query.select_related("content_type").values_list(
                    "content_type__app_label", "codename"
                )
            )
            return req._perms

        window_info_cls.user = property(get_user)
        window_info_cls.has_perm = has_perm
        window_info_cls.perms = property(get_perms)


class BrowserMiddleware(WindowInfoMiddleware):
    """add attributes related to the browser (currently only the HTTP_USER_AGENT header)"""

    def from_request(self, request, window_info):
        window_info.user_agent = request.META.get("HTTP_USER_AGENT", "")

    def new_window_info(self, window_info):
        window_info.user_agent = ""

    def to_dict(self, window_info):
        return {"user_agent": window_info.user_agent}

    def from_dict(self, window_info, values):
        window_info.user_agent = values.get("user_agent", "")

    def get_context(self, window_info):
        return {
            "df_user_agent": window_info.user_agent,
            "messages": [],
            "DEFAULT_MESSAGE_LEVELS": DEFAULT_LEVELS,
        }


class Djangoi18nMiddleware(WindowInfoMiddleware):
    """Add attributes required for using i18n-related functions."""

    def from_request(self, request, window_info):
        # noinspection PyTypeChecker
        if getattr(request, "session", None):
            window_info.language_code = get_language_from_request(request)
        else:
            window_info.language_code = settings.LANGUAGE_CODE

    def new_window_info(self, window_info):
        window_info.language_code = None

    def to_dict(self, window_info):
        return {"language_code": window_info.language_code}

    def from_dict(self, window_info, values):
        window_info.language_code = values.get("language_code")

    def get_context(self, window_info):
        return {
            "LANGUAGES": settings.LANGUAGES,
            "LANGUAGE_CODE": window_info.language_code,
            "LANGUAGE_BIDI": translation.get_language_bidi(),
        }
