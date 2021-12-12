df_websockets
=============

`df_websockets` extends [django-channels](https://channels.readthedocs.io) to simplify communications between 
clients and servers and to process heavy tasks in background processes.
Background processes can use [celery](https://docs.celeryproject.org/en/stable/), `django-channels` runners, or simply different processes or threads.

`df_websockets` is based on two main concepts:

* _signals_, that are functions triggered both on the server or the browser  window by either the server or the client,
* _topics_ to allow the server to send signals to any group of browser windows.

Signals are exchanged between the browser window and the server using a single websocket.
Signals triggered by the browser on the server are processed as background tasks (so the websocket endpoint does almost nothing).
Signals triggered by the server can be processed as other Celery tasks and as Javascript functions on the browser.


Requirements and installation
-----------------------------

`df_websockets` works with:

  * Python >= 3.6,
  * django >= 2.0,
  * django-channels >= 2.0.


For production use or any multiprocess setup (even in development mode), you also need:

  * [redis](https://redis.io) >= 5.0,
  * channels_redis.

If you want to process signals in Celery tasks rather in Channel workers, you need to setup a Celery infrastructure:
[Celery setup](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html).

```bash
python -m pip install df_websockets
```

In your settings, you must add the following values:
```python
# the ASGI application to use with gunicorn or daphne
ASGI_APPLICATION = "df_websockets.routing.application"
# add the required Middleware
MIDDLEWARES = [..., "df_websockets.middleware.WebsocketMiddleware", ...]
INSTALLED_APPS = [..., "channels", "df_websockets", ...]
WEBSOCKET_WORKERS = "thread"
# a channel layer, required by channels_redis
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('localhost', 6379)],
        },
    },
}
```

If you use `df_config` and you use a local Redis, you have nothing to do: settings are automatically set and everything is working as soon as a Redis is running on your machine.

Now, include `js/df_websockets.min.js` in your HTML and call `df_websockets.tasks.set_websocket_topics(request)` somewhere in the Django view.
A bidirectionnal websocket connection will be established in your page.

You can start the development server:
```bash
python manage.py runserver
```


If you use Channels workers (WEBSOCKET_WORKERS = "channels"), you also need to start a Channel worker:
```bash
python manage.py run_worker celery
```
If you use Celery (WEBSOCKET_WORKERS = "celery"), you also need to start a Celery worker:
```bash
python manage.py worker -Q celery
```

basic usage
-----------

A _signal_ is a string attached to Python or Javascript functions. When this signal is triggered, all these functions are called.
Of course, you can target the platforms on which the functions will be executed: the server (for Python code) or chosen browser windows.

First, we connect our code to the signal `"myproject.first_signal"`.
```python
from df_websockets.decorators import everyone, signal
import time

@signal(path="myproject.first_signal", is_allowed_to=everyone, queue="celery")
def my_first_signal(window_info, content=None):
    print(content)

@signal(path="myproject.first_signal", is_allowed_to=everyone, queue="slow")
def my_first_signal_slow(window_info, content=None):
    time.sleep(100)
    print(content)
```

```javascript
/* static file "js/df_websockets.min.js" must be included first */
document.addEventListener("DOMContentLoaded", () => {
    window.DFSignals.connect('myproject.first_signal', (opts) => {
        console.warn(opts.content);
    });
});
```

Now, we can trigger this signal to call this functions.
In both cases, both functions will be called on the server and in the browser window.
```javascript
window.DFSignals.call('myproject.first_signal', {content: "Hello from browser"});
```

```python
from df_websockets.tasks import WINDOW, trigger, SERVER
from df_websockets.decorators import everyone, signal
from django.http.response import HttpResponse

def any_view(request):  # this is a standard Django view
    trigger(request, 'myproject.first_signal', to=[SERVER, WINDOW], content="hello from a view")
    return HttpResponse()

@signal(path="myproject.second_signal", is_allowed_to=everyone, queue="slow")
def second_signal(window_info):
    trigger(window_info, 'myproject.first_signal', to=[SERVER, WINDOW], content="hello from Celery")
```

In this case, the `to` parameter targets both the server and the window.
You can even open a shell and call `df_websockets.tasks.trigger(None, 'myproject.first_signal', to=[BROADCAST], content="hello from a shell")`.
All open windows will react.

Topics
------

When the server triggers a signal, it can select if the signal is called on the server or on some browser windows.

A Django view using this signal system must call `set_websocket_topics` to add some ”topics” to this view.
`js/df_websockets.min.js` must also be added to the resulting HTML. 

```python
from df_websockets.tasks import set_websocket_topics

def any_view(request):  # this is a standard Django view
    # useful code
    obj1 = MyModel.objects.get(id=42)
    set_websocket_topics(request, [obj1])
    return TemplateResponse("my/template.html", {})
```

`obj1` must be a Python object that is handled by the `WEBSOCKET_TOPIC_SERIALIZER` function. By default, any string and Django models are valid.
Each window also has a unique identifier that is automatically added to this list, as well as the connected user id and the `BROADCAST`.

The following code will call the JS function on every browser window having the `obj` topic and to the displayed window.
```python
from df_websockets.tasks import WINDOW, trigger
from df_websockets.tasks import set_websocket_topics

def another_view(request, obj_id):
    obj = MyModel.objects.get(id=42)
    trigger(request, 'myproject.first_signal', to=[WINDOW, obj], content="hello from a view")
    set_websocket_topics(request, [other_topics])
    return HttpResponse()
```

There are three special values:

* `df_websockets.tasks.WINDOW`: the original browser window,
* `df_websockets.tasks.USER`: all windows currently displayed by the connected user,
* `df_websockets.tasks.BROADCAST`: all active windows.

Some information about the original window (like its unique identifier or the connected user) must be provided to the triggered Python code, allowing it to trigger JS events on any selected window.  
These data are stored in the `WindowInfo` object, automatically built from the HTTP request by the trigger function and provided as first argument to the triggered code.
The `trigger` function accepts `WindowInfo` or `HTTPRequest` objects as first argument.


HTML forms
----------

`df_websockets` comes with some helper functions when you signals to be trigger on the server when a form is submitted or changed.
Assuming that you have a `signals.py` file that contains:
```python
from df_websockets.decorators import signal
from df_websockets.tasks import WINDOW, trigger
from df_websockets.utils import SerializedForm
from django import forms


class MyForm(forms.Form): 
    title = forms.CharField()

@signal(path='signal.name')
def my_signal_function(window_info, form_data: SerializedForm(MyForm)=None, title=None, id=None):
    print(form_data and form_data.is_valid())
    trigger(window_info, 'myproject.first_signal', to=WINDOW, title=title)

@signal(path='signal.name')
def my_signal_function_raw(window_info, form_data=None, title=None, id=None):
    print(form_data and form_data.is_valid())
    trigger(window_info, 'myproject.first_signal', to=WINDOW, title=title)
```


Using on a HTML form:
```html
<form data-df-signal='[{"name": "signal.name", "on": "change", "form": "form_data", "opts": {"id": 42} }]'>
    <input type="text" name="title" value="df_websockets">
</form>
```

or, using the Django templating system:

```html
{% load websockets %}
<form {% js_call "signal.name" on="change" form="form_data" id=42 %}>
    <input type="text" name="title" value="df_websockets">
</form>
```

When the field "title" is modified, `my_signal_function(window_info, form_data = [{"name": "title", "value": "df_websockets"}], id=43)` is called.



Using on a HTML form input field:
```html
<form>
    <input type="text" name="title" data-df-signal='[{"name": "signal.name", "on": "change", "value": "title", "opts": {"id": 42} }]'>
</form>
```

or, using the Django templating system:

```html
{% load websockets %}
<form>
    <input type="text" name="title" {% js_call "signal.name" on="change" value="title" id=42 %}>
</form>
```

When the field "title" is modified, `my_signal_function(window_info, title="new title value", id=43)` is called.



Testing signals
---------------

The signal framework requires a working Redis and a worker process. However, if you only want to check if a signal
has been called in unitary tests, you can use :class:`df_websockets.utils.SignalQueue`.
Both server-side and client-side signals are kept into memory:

* `df_websockets.testing.SignalQueue.ws_signals`,

    * keys are the serialized topics
    * values are lists of tuples `(signal name, arguments as dict)`

* `df_websockets.testing.SignalQueue.python_signals`

    * keys are the name of the queue
    * values are lists of `(signal_name, window_info_dict, kwargs=None, from_client=False, serialized_client_topics=None, to_server=False, queue=None)`

      * `signal_name` is … the name of the signal
      * `window_info_dict` is a WindowInfo serialized as a dict,
      * `kwargs` is a dict representing the signal arguments,
      * `from_client` is `True` if this signal has been emitted by a web browser,
      * `serialized_client_topics` is not `None` if this signal must be re-emitted to some client topics,
      * `to_server` is `True` if this signal must be processed server-side,
      * `queue` is the name of the selected Celery queue.

```python
from df_websockets.tasks import trigger, SERVER
from df_websockets.window_info import WindowInfo
from df_websockets.testing import SignalQueue

from df_websockets.decorators import signal
# noinspection PyUnusedLocal
@signal(path='test.signal', queue='demo-queue')
def test_signal(window_info, value=None):
  print(value)

wi = WindowInfo()
with SignalQueue() as fd:
  trigger(wi, 'test.signal1', to=[SERVER, 1], value="value1")
  trigger(wi, 'test.signal2', to=[SERVER, 1], value="value2")

# fd.python_signals looks like {'demo-queue': [ ['test.signal1', {…}, {'value': 'value1'}, False, None, True, None], 
# # ['test.signal2', {…}, {'value': 'value2'}, False, None, True, None]]}
# fd.ws_signals looks like {'-int.1': [('test.signal1', {'value': 'value1'}), ('test.signal2', {'value': 'value2'})]}
```

JavaScript signals
------------------

Many [JS signals](https://github.com/d9pouces/df_websockets/blob/master/npm/df_websockets/base.js) are available out-of-the-box.
These signals can be triggered either by the JS code or by the Python code.
For example, you can update the content of a HTML node with the following lines:

```python
from df_websockets.tasks import trigger, WINDOW
from df_websockets.decorators import signal

@signal(path='test.signal', queue='demo-queue')
def test_signal(window_info, word="hellow"):
    trigger(window_info, 'html.content', to=WINDOW, selector="#obj", content= "<span>%s</span>" % word)
```

```javascript
window.DFSignals.call('html.content', {selector: "#obj", content: "<span>hello</span>"});
```

Please read the content of `npm/df_websockets/base.js` for the whole list of available signals. 
You can also create some shortcuts for the most common signals.


Checklist 
---------

Everything must be correctly setup to have working signals.

The first step is to test tasks from the command-line:

1. Redis is running and accepting connections
2. Celery is working
2. at least one worker is running with all required queues
3. the triggered signal is exists
4. open a console `python manage.py shell` and manually trigger a task
```python
from df_websockets.tasks import trigger, SERVER
from df_websockets.window_info import WindowInfo
trigger(WindowInfo(), 'test.signal', to=[SERVER], value="value2")
```


The second step is to check the web part:

1. the web server must be running and accepting connections
2. Celery is working
2. at least one worker is running with all required queues
3. the triggered signal exists
3. `df_websockets.middleware.WebsocketMiddleware` is included
4. check the used domain name, since tokens are passed through cookies: **"localhost" is different than "127.0.0.1"**
5. `df_websockets.tasks.set_websocket_topics` is used somewhere in the view
6. `static/js/df_websockets.min.js` is included in the page
7. check if the WS tries to connect
8. check if the WS is connected
4. open a console `python manage.py shell` and manually trigger a task
```python
from df_websockets.tasks import trigger, BROADCAST
from df_websockets.window_info import WindowInfo
trigger(WindowInfo(), 'html.text', to=[BROADCAST], selector="body", content= "<span>hello</span>")
```

Do not hesitate to use a verbose logging:
```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": (
                "%(asctime)s [%(process)d] [%(levelname)s] "
                + "pathname=%(pathname)s lineno=%(lineno)s "
                + "funcname=%(funcName)s %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
        },
        "nocolor": {
            "()": "logging.Formatter",
            "fmt": "%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
    },
    "handlers": {
        "stdout.info": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
            "formatter": "verbose",
        },
        "stderr.debug.django.server": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "stream": "ext://sys.stderr",
            "formatter": "django.server",
        },
    },
    "loggers": {
        "django": {"handlers": [], "level": "INFO", "propagate": True},
        "django.db": {"handlers": [], "level": "INFO", "propagate": True},
        "django.db.backends": {"handlers": [], "level": "INFO", "propagate": True},
        "django.request": {"handlers": [], "level": "DEBUG", "propagate": True},
        "django.security": {"handlers": [], "level": "INFO", "propagate": True},
        "df_websockets.signals": {"handlers": [], "level": "DEBUG", "propagate": True},
        "gunicorn.error": {"handlers": [], "level": "DEBUG", "propagate": True},
        "pip.vcs": {"handlers": [], "level": "INFO", "propagate": True},
        "py.warnings": {
            "handlers": [],
            "level": "INFO",
            "propagate": True,
        },
        "daphne.cli": {"handlers": [], "level": "INFO", "propagate": True},
        "mail.log": {"handlers": [], "level": "INFO", "propagate": True},
        "aiohttp.access": {
            "handlers": ["stderr.debug.django.server"],
            "level": "INFO",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["stderr.debug.django.server"],
            "level": "INFO",
            "propagate": False,
        },
        "django.channels.server": {
            "handlers": ["stderr.debug.django.server"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.access": {
            "handlers": ["stderr.debug.django.server"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {"handlers": ["stdout.info"], "level": "DEBUG"},
}

```