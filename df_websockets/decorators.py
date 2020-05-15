"""Decorators to declare signals and remote functions
==================================================

ALso define common functions for allowing (or not) signal calls to user, and several tools for checking arguments
provided to the signal (or function).

Decorators
----------

Three decorators are provided, for creating signals, websocket functions or special signals for validating forms.
Original functions are left unmodified by the decorators.
These decorators instantiate a :class:`df_websockets.decorators.Connection` object and stores it in the
corresponding dict (`REGISTERED_FUNCTIONS` or `REGISTERED_SIGNALS`).

Restrict signal/function use
----------------------------

When creating a connection, you provide a callable that checks if the browser is allowed to call this code.
By default, the registered code can only be called from Python code.
The callable takes three arguments:

  * the called :class:`df_websockets.decorators.Connection` (signal or ws function),
  * the :class:`df_websockets.window_info.WindowInfo` object,
  * the kwarg dict with unmodified arguments.

Argument validators
-------------------

The registered Python code can use py3 annotation for specifying data types.

.. code-block:: python

  from df_websockets.decorators import Choice, RE, SerializedForm
  from django import forms

  class MyForm(forms.Form):
      test = forms.CharField()

  @signal(path='demo.signal')
  def my_signal(window_info, kwarg1: Choice([1, 2], int)=1, kwarg2: Re('^\\d+$', int)=2,
          kwarg3: SerializedForm(MyForm)):
     assert isinstance(kwarg1, int)
     assert isinstance(kwarg2, int)
     assert isinstance(kwarg3, MyForm)

  trigger(window_info, 'demo.signal', to=[SERVER], kwarg1="1", kwarg2="12312", kwarg3=[{'value': '12', 'name': 'test'}])


"""

# ##############################################################################
#  This file is part of Interdiode                                             #
#                                                                              #
#  Copyright (C) 2020 Matthieu Gallet <matthieu.gallet@19pouces.net>           #
#  All Rights Reserved                                                         #
#                                                                              #
# ##############################################################################

import io
import logging
import mimetypes
import os
import random
import re
from inspect import signature

from df_websockets import ws_settings
from df_websockets.utils import SerializedForm
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms import FileField
from django.http import QueryDict

logger = logging.getLogger("df_websockets.signals")

REGISTERED_SIGNALS = {}
REGISTERED_FUNCTIONS = {}


class DynamicQueueName:
    """Allow to dynamically select a Celery queue when the signal is called.
    You can use it if all signals of a user must be processed by the same worker, but you still
      want to dispatch signals to several workers.

    """

    def __call__(self, connection, window_info, original_kwargs):
        """called for each signal call to dispatch this connection"""
        raise NotImplementedError

    def get_available_queues(self):
        """return the set of all queues that can be returned by the `__call__` method.
         However, if this method is not implemented, the impact is currently limited:
           * the monitoring view will not display all required queues,
           * the systemd service files (provided by the `packaging` command) will not create all required workers.
         """
        return {ws_settings.CELERY_DEFAULT_QUEUE}


class RandomDynamicQueueName(DynamicQueueName):
    """Return a random queue on each signal call.

     This class is somewhat useless since you could just run more workers on the same queue.

      >>> q = RandomDynamicQueueName('prefix-', 2)
      >>> q.get_available_queues() == {'prefix-0', 'prefix-1'}
      True

      >>> q(None, None, None) in {'prefix-0', 'prefix-1'}
      True

    """

    def __init__(self, prefix: str, size: int):
        """

        :param prefix: prefix of the queue
        :param size: number of available queues
        """
        self.prefix = prefix
        self.size = size

    def __call__(self, connection, window_info, original_kwargs):
        return "%s%d" % (self.prefix, random.randint(0, self.size - 1))

    def get_available_queues(self):
        return {"%s%d" % (self.prefix, x) for x in range(self.size)}


# noinspection PyUnusedLocal
def server_side(connection, window_info, kwargs):
    """never allows a signal to be called from WebSockets; this signal can only be called from Python code.
    This is the default choice.

    >>> @signal(is_allowed_to=server_side)
    ... def my_signal(window_info, arg1=None):
    ...     # noinspection PyUnresolvedReferences
    ...     print(window_info, arg1)
    """
    return False


# noinspection PyUnusedLocal
def everyone(connection, window_info, kwargs):
    """allow everyone to call a Python WS signal or remote function

    >>> @signal(is_allowed_to=everyone)
    ... def my_signal(request, arg1=None):
    ...     # noinspection PyUnresolvedReferences
    ...     print(request, arg1)
    """
    return True


# noinspection PyUnusedLocal
def is_authenticated(connection, window_info, kwargs):
    """restrict a WS signal or a WS function to authenticated users

    >>> @signal(is_allowed_to=is_authenticated)
    ... def my_signal(request, arg1=None):
    ...     # noinspection PyUnresolvedReferences
    ...     print(request, arg1)
    """
    return window_info and window_info.is_authenticated


# noinspection PyUnusedLocal
def is_anonymous(connection, window_info, kwargs):
    """restrict a WS signal or a WS function to anonymous users

    >>> @signal(is_allowed_to=is_anonymous)
    ... def my_signal(request, arg1=None):
    ...     # noinspection PyUnresolvedReferences
    ...     print(request, arg1)
        """
    return window_info and window_info.is_anonymous


# noinspection PyUnusedLocal
def is_staff(connection, window_info, kwargs):
    """restrict a WS signal or a WS function to staff users

    >>> @signal(is_allowed_to=is_staff)
    ... def my_signal(request, arg1=None):
    ...     # noinspection PyUnresolvedReferences
    ...     print(request, arg1)
    """
    return window_info and window_info.is_staff


# noinspection PyUnusedLocal
def is_superuser(connection, window_info, kwargs):
    """restrict a WS signal or a WS function to superusers

    >>> @signal(is_allowed_to=is_superuser)
    ... def my_signal(request, arg1=None):
    ...     # noinspection PyUnresolvedReferences
    ...     print(request, arg1)
    """
    return window_info and window_info.is_superuser


# noinspection PyPep8Naming
class has_perm:
    """restrict a WS signal or a WS function to users with permission "perm"

    >>> @signal(is_allowed_to=has_perm('app_label.codename'))
    ... def my_signal(request, arg1=None):
    ...     # noinspection PyUnresolvedReferences
    ...     print(request, arg1)
    """

    def __init__(self, perm):
        self.perm = perm

    # noinspection PyUnusedLocal
    def __call__(self, connection, window_info, kwargs):
        return window_info and window_info.has_perm(self.perm)


class Connection:
    """Parent class of a registered signal or remote function.
     Do not use it directly."""

    required_function_arg = "window_info"

    def __init__(self, fn, path=None, is_allowed_to=server_side, queue=None):
        self.function = fn
        if not path:
            if getattr(fn, "__module__", None) and getattr(fn, "__name__", None):
                path = "%s.%s" % (fn.__module__, fn.__name__)
            elif getattr(fn, "__name__", None):
                path = fn.__name__
        self.path = str(path)
        if not re.match(r"^([_a-zA-Z]\w*)(\.[_a-zA-Z]\w*)*$", self.path):
            raise ValueError("Invalid identifier: %s" % self.path)
        self.is_allowed_to = is_allowed_to
        self.queue = queue or ws_settings.CELERY_DEFAULT_QUEUE
        self.accept_kwargs = False
        self.argument_types = {}
        self.required_arguments_names = set()
        self.optional_arguments_names = set()
        self.accepted_argument_names = set()
        self.signature_check(fn)
        # noinspection PyTypeChecker
        if hasattr(fn, "__name__"):
            self.__name__ = fn.__name__

    def signature_check(self, fn):
        """Analyze the signature of the registered Python code, and store the annotations.
        Check if the first argument is `window_info`.
        """
        # fetch signature to analyze arguments
        sig = signature(fn)
        required_arg_is_present = False
        for key, param in sig.parameters.items():
            if key == self.required_function_arg:
                required_arg_is_present = True
                continue
            if param.kind == param.VAR_KEYWORD:  # corresponds to "fn(**kwargs)"
                self.accept_kwargs = True
            elif param.kind == param.VAR_POSITIONAL:  # corresponds to "fn(*args)"
                raise ValueError("Cannot connect a signal using the *%s syntax" % key)
            elif (
                param.default == param.empty
            ):  # "fn(foo)" : kind = POSITIONAL_ONLY or POSITIONAL_OR_KEYWORD
                self.required_arguments_names.add(key)
                if param.annotation != param.empty and callable(param.annotation):
                    self.argument_types[key] = param.annotation
                self.accepted_argument_names.add(key)
            else:  # "fn(foo=bar)" : kind = POSITIONAL_OR_KEYWORD or KEYWORD_ONLY
                self.optional_arguments_names.add(key)
                self.accepted_argument_names.add(key)
                if param.annotation != param.empty and callable(param.annotation):
                    self.argument_types[key] = param.annotation
        if self.required_function_arg and not required_arg_is_present:
            msg = '%s(%s) must takes "%s" as first argument' % (
                self.__class__.__name__,
                self.path,
                self.required_function_arg,
            )
            raise ValueError(msg)

    def check(self, kwargs):
        """Check the provided kwargs and apply provided annotations to it.
        Return `None` if something is invalid (like an error raised by an annotation or a missing argument).
        """
        cls = self.__class__.__name__
        for k, v in self.argument_types.items():
            try:
                if k in kwargs:
                    kwargs[k] = v(kwargs[k])
            except ValueError:
                logger.warning(
                    '%s("%s"): Invalid value %r for argument "%s".'
                    % (cls, self.path, kwargs[k], k)
                )
                return None
            except TypeError:
                logger.warning(
                    '%s("%s"): Invalid value %r for argument "%s".'
                    % (cls, self.path, kwargs[k], k)
                )
                return None
        for k in self.required_arguments_names:
            if k not in kwargs:
                logger.warning(
                    '%s("%s"): Missing required argument "%s".' % (cls, self.path, k)
                )
                return None
        if not self.accept_kwargs:
            for k in kwargs:
                if k not in self.accepted_argument_names:
                    logger.warning(
                        '%s("%s"): Invalid argument "%s".' % (cls, self.path, k)
                    )
                    return None
        return kwargs

    def __call__(self, window_info, **kwargs):
        return self.function(window_info, **kwargs)

    def register(self):
        """Register the Python code to the right dict."""
        raise NotImplementedError

    def get_queue(self, window_info, original_kwargs):
        """Provide the Celery queue name as a string."""
        if callable(self.queue):
            return str(self.queue(self, window_info, original_kwargs))
        return str(self.queue) or ws_settings.CELERY_DEFAULT_QUEUE


class SignalConnection(Connection):
    """represents a connected signal.
    """

    def register(self):
        """register the signal into the `REGISTERED_SIGNALS` dict """
        REGISTERED_SIGNALS.setdefault(self.path, []).append(self)

    def call(self, window_info, **kwargs):
        from df_websockets.tasks import trigger_signal, SERVER

        trigger_signal(window_info, self.path, to=SERVER, kwargs=kwargs)


class FunctionConnection(Connection):
    """represent a WS function """

    def register(self):
        """register the WS function into the `REGISTERED_FUNCTIONS` dict """
        REGISTERED_FUNCTIONS[self.path] = self


class FormValidator(FunctionConnection):
    """Special signal, dedicated to dynamically validate a HTML form.

    However, files cannot be sent in the validation process.
    """

    def signature_check(self, fn):
        """override the default method for checking the arguments, since they are independent from the Django Form.
        """
        if not isinstance(fn, type) or not issubclass(fn, forms.BaseForm):
            raise ValueError("validate_form only apply to Django Forms")
        self.required_arguments_names = set()
        self.optional_arguments_names = {"data"}
        self.accepted_argument_names = {"data"}

    def __call__(self, window_info, data=None):
        form = SerializedForm(self.function)(data)
        valid = form.is_valid()
        return {
            "valid": valid,
            "errors": {
                f: e.get_json_data(escape_html=False) for f, e in form.errors.items()
            },
            "help_texts": {
                f: e.help_text for (f, e) in form.fields.items() if e.help_text
            },
        }


def signal(
    fn=None, path=None, is_allowed_to=server_side, queue=None, cls=SignalConnection
):
    """Decorator to use for registering a new signal.
    This decorator returns the original callable as-is.

    TODO: add a special queue SYNC
    """

    def wrapped(fn_):
        wrapper = cls(fn=fn_, path=path, is_allowed_to=is_allowed_to, queue=queue)
        wrapper.register()
        return fn_

    if fn is not None:
        wrapped = wrapped(fn)
    return wrapped


# noinspection PyShadowingBuiltins
def function(fn=None, path=None, is_allowed_to=server_side, queue=None):
    """Allow the following Python code to be called from the JavaScript code.
The result of this function is serialized (with JSON and `settings.WEBSOCKET_SIGNAL_ENCODER`) before being
sent to the JavaScript part.

.. code-block:: python

  from df_websockets.decorators import function, everyone

  @function(path='myproject.myfunc', is_allowed_to=everyone)
  def myfunc(window_info, arg=None)
      print(arg)
      return 42

The this function can be called from your JavaScript code:

.. code-block:: javascript

  $.dfws.myproject.myfunc({arg: 3123}).then(function(result) { alert(result); });


"""
    return signal(
        fn=fn,
        path=path,
        is_allowed_to=is_allowed_to,
        queue=queue,
        cls=FunctionConnection,
    )


def validate_form(form_cls=None, path=None, is_allowed_to=server_side, queue=None):
    """
    Decorator for automatically validating HTML forms. Just add it to your Python code and set the 'onchange'
    attribute to your HTML code. The `path` argument should be unique to your form class.

    :param form_cls: any subclass of :class:`django.forms.Form`
    :param path: unique name of your form
    :param is_allowed_to: callable for restricting the use of the form validation
    :param queue: name (or callable) for ensuring small response times

.. code-block:: python

    from df_websockets.decorators import everyone, validate_form

    @validate_form(path='df_websockets.validate.search', is_allowed_to=everyone, queue='fast')
    class MyForm(forms.Form):
        name = forms.CharField()
        ...


.. code-block:: html

    <form onchange="$.df.validateForm(this, 'df_websockets.validate.search');"  action="?" method="post">
        {% csrf_token %}
        {% bootstrap_form form %}
        <input type="submit" class="btn btn-primary" value="{% trans 'Search' %}">
    </form>

    """
    if path is None or is_allowed_to is server_side:
        # @validate_form
        # class MyForm(forms.Form):
        #     ...
        raise ValueError(
            "is_allowed_to and path are not configured for the validate_form decorator"
        )

    def wrapped(form_cls_):
        wrapper = FormValidator(
            form_cls_, path=path, is_allowed_to=is_allowed_to, queue=queue
        )
        wrapper.register()
        return form_cls_

    if form_cls:
        return wrapped(form_cls)
    return wrapped
