df_websockets
=============

Based on [django-channels](https://channels.readthedocs.io) and [celery](https://docs.celeryproject.org/en/stable/), df_websockets simplifies communication between 
clients and servers and processing tasks in background processes.

df_websockets is based on two main ideas:

* _signals_, that are functions triggered both on the server or the browser  window by either the server or the client,
* _topics_ to allow the server to send signals to any group of browser windows.

Signals are exchanged between the browser window and the server using a single websockets. Signals triggered by the browser on the server are processed as Celery tasks (so the websocket endpoint does almost nothing).
Signals triggered by the server can be processed as other Celery tasks and as Javascript functions on the browser.


Requirements and installation
-----------------------------

df_config works with:

  * Python 3.6+,
  * django 2.0+,
  * celery 4.0+,
  * redis,
  * django-channels 2.0+,
  * channels_redis.

You also need a working [redis server](https://redis.io) and [Celery setup](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html).

```bash
pip install df_websockets
```

In your settings, if you do not use `df_config`, you must add the following values:
```python
ASGI_APPLICATION = "df_websockets.routing.application"
# the ASGI application to use with gunicorn or daphne
MIDDLEWARES = [..., "df_websockets.middleware.WebsocketMiddleware", ...]
# a required middleware
CELERY_APP = "df_websockets"
# the celery application
CELERY_DEFAULT_QUEUE = "celery"
# the default queue to use
WEBSOCKET_REDIS_CONNECTION = {'host': 'localhost', 'port': 6379, 'db': 3, 'password': ''}
WEBSOCKET_REDIS_EXPIRE = 36000
WEBSOCKET_REDIS_PREFIX = "ws"
WEBSOCKET_SIGNAL_DECODER = "json.JSONDecoder"
WEBSOCKET_SIGNAL_ENCODER = "django.core.serializers.json.DjangoJSONEncoder"
WEBSOCKET_TOPIC_SERIALIZER = "df_websockets.topics.serialize_topic"
WINDOW_INFO_MIDDLEWARES = ["df_websockets.ws_middleware.WindowKeyMiddleware", "df_websockets.ws_middleware.DjangoAuthMiddleware", "df_websockets.ws_middleware.Djangoi18nMiddleware", "df_websockets.ws_middleware.BrowserMiddleware",]
# equivalent to MIDDLEWARES, but for websockets
WEBSOCKET_URL = "/ws/"
# the endpoint for the websockets
```
If you use `df_config` and you use a local Redis, you have nothing to do: settings are automatically set and everything is working as soon as a Redis is running on your machine.

You can start a Celery worker and the development server:
```bash
python manage.py worker 
python manage.py runserver

```

basic usage
-----------

A _signal_ is a string attached to Python or Javascript functions. When this signal is triggered, all these functions are called.
Of course, you can target the platforms on which the functions will be executed: the server (for Python code) or any set of browser windows.

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
    DFSignals.connect('myproject.first_signal', (opts) => {
        console.warn(opts.content);
    });
});
```

Now, we can trigger this signal to call this functions.

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

```javascript
DFSignals.call('myproject.first_signal', {content: "Hello from browser"});
```