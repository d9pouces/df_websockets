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
from html import escape
from typing import Dict, Optional

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


class JSCall:
    def __init__(
        self,
        name: str,
        on: Optional[str] = None,
        opts: Optional[Dict] = None,
        form: Optional[str] = None,
        value: Optional[str] = None,
        prevent: Optional[bool] = None,
    ):
        self.name = name
        self.on = on
        self.opts = opts
        self.form = form
        self.value = value
        self.prevent = prevent

    def __str__(self):
        opts = self.get_json_dict()
        return json.dumps(opts)

    def get_json_dict(self):
        opts = {"name": self.name, "prevent": self.prevent}
        for attr in ("on", "opts", "form", "value"):
            if getattr(self, attr):
                opts[attr] = getattr(self, attr)
        return opts


@register.simple_tag()
def js_calls(*calls):
    values = [x.get_json_dict() for x in calls]
    return mark_safe(' data-df-signal="%s" ' % escape(json.dumps(values)))


@register.simple_tag()
def js_call(name, on=None, form=None, value=None, **kwargs):
    call = JSCall(name, on=on, opts=kwargs, form=form, value=value)
    return js_calls(call)
