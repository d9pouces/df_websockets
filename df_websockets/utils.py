# ##############################################################################
#  This file is part of Interdiode                                             #
#                                                                              #
#  Copyright (C) 2020 Matthieu Gallet <matthieu.gallet@19pouces.net>           #
#  All Rights Reserved                                                         #
#                                                                              #
# ##############################################################################
import hashlib
import io
import mimetypes
import os
import re
from typing import Union

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import QueryDict


class RE:
    """ used to check if a string value matches a given regexp.

    Example (requires Python 3.2+), for a function that can only handle a string of the form 123a456:

    .. code-block:: python

        @signal(path='myproject.signals.test')
        def test(window_info, value: RE('\\d{3}a\\d{3}')):
            pass

    Your code won't be called for values like "abc".


    :param value: regexp pattern
    :type value: `str`
    :param caster: if not `None`, any callable applied to the value (if valid)
    :type caster: `callable` or `None`
    :param flags: regexp flags passed to `re.compile`
    :type flags: `int`
    """

    def __init__(self, value, caster=None, flags=0):
        self.caster = caster
        self.regexp = re.compile(value, flags=flags)

    def __call__(self, value):
        matcher = self.regexp.match(str(value))
        if not matcher:
            raise ValueError
        value = matcher.group(1) if matcher.groups() else value
        return self.caster(value) if self.caster else value


class Choice:
    """ used to check if a value is among some valid choices.

    Example (requires Python 3.2+), for a function that can only two values:

    .. code-block:: python

        @signal(path='myproject.signals.test')
        def test(window_info, value: Choice([True, False])):
            pass

    Your code wan't be called if value is not True or False.

    :param caster: callable to convert the provided deserialized JSON data before checking its validity.
    """

    def __init__(self, values, caster=None):
        self.values = set(values)
        self.caster = caster

    def __call__(self, value):
        value = self.caster(value) if self.caster else value
        if value not in self.values:
            raise ValueError
        return value


class SerializedForm:
    """Transform values sent by JS to a Django form.

    Given a form and a :class:`list` of :class:`dict`, transforms the :class:`list` into a
    :class:`django.http.QueryDict` and initialize the form with it.

    >>> from django import forms
    >>> class SimpleForm(forms.Form):
    ...    field = forms.CharField()
    ...
    >>> x = SerializedForm(SimpleForm)
    >>> form = x([{'name': 'field', 'value': 'object'}])
    >>> form.is_valid()
    True

    How to use it with Python3:

    .. code-block:: python

        @signal(path='myproject.signals.test')
        def test(window_info, value: SerializedForm(SimpleForm), other: int):
            print(value.is_valid())

    How to use it with Python2:

    .. code-block:: python

        @signal(path='myproject.signals.test')
        def test(window_info, value, other):
            value = SerializedForm(SimpleForm)(value)
            print(value.is_valid())


    On the JS side, you can serialize the form with JQuery:

    .. code-block:: html

        <form onsubmit="return $.df.call('myproject.signals.test', {value: $(this).serializeArray(), other: 42})">
            <input name='field' value='test' type='text'>
        </form>


    """

    def __init__(self, form_cls):
        self.form_cls = form_cls

    def __call__(self, value, *args, **kwargs):
        """
        :param value:
        :type value: :class:`list` of :class:`dict`
        :return:
        :rtype: :class:`django.forms.Form`
        """
        from django.forms import FileField
        if value is None:
            return self.form_cls(*args, **kwargs)

        post_data = QueryDict("", mutable=True)
        file_data = QueryDict("", mutable=True)
        for obj in value:
            name = obj["name"]
            value = obj["value"]
            if name in self.form_cls.base_fields and isinstance(
                    self.form_cls.base_fields[name], FileField
            ):
                mimetypes.init()
                basename = os.path.basename(value)
                (type_, __) = mimetypes.guess_type(basename)
                # it's a file => we need to simulate an uploaded one
                content = InMemoryUploadedFile(
                    io.BytesIO(b"\0"),
                    name,
                    basename,
                    type_ or "application/binary",
                    1,
                    "utf-8",
                )
                file_data.update({name: content})
            else:
                post_data.update({name: value})
        return self.form_cls(post_data, file_data, *args, **kwargs)


def valid_topic_name(x: Union[str, bytes]) -> str:
    if isinstance(x, str):
        x = x.encode("utf-8")
    return hashlib.sha256(x).hexdigest()
