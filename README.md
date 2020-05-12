df_websockets
=============

Based on [django-channels](https://channels.readthedocs.io), df_websockets simplifies communication between 
clients and servers.

df_websockets is based on two main ideas:

* _signals_, that are functions triggered both on the server or the browser  window by either the server or the client,
* _topics_ to allow the server to send signals to any group of browser windows.


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
MIDDLEWARES = [..., "df_websockets.middleware.WebsocketMiddleware", ...]
CELERY_APP = "df_websockets"
CELERY_DEFAULT_QUEUE = "celery"
WEBSOCKET_REDIS_CONNECTION = {'host': 'localhost', 'port': 6379, 'db': 3, 'password': ''}
WEBSOCKET_REDIS_EXPIRE = 36000
WEBSOCKET_REDIS_PREFIX = "ws"
WEBSOCKET_SIGNAL_DECODER = "json.JSONDecoder"
WEBSOCKET_SIGNAL_ENCODER = "django.core.serializers.json.DjangoJSONEncoder"
WEBSOCKET_TOPIC_SERIALIZER = "df_websockets.topics.serialize_topic"
WINDOW_INFO_MIDDLEWARES = ["df_websockets.ws_middleware.WindowKeyMiddleware", "df_websockets.ws_middleware.DjangoAuthMiddleware", "df_websockets.ws_middleware.Djangoi18nMiddleware", "df_websockets.ws_middleware.BrowserMiddleware",]
WEBSOCKET_URL = "/ws/"
```
If you use `df_config` and you use a local Redis, you have nothing to do: settings are automatically set.

basic usage
-----------

A _signal_ is a string attached to Python or Javascript functions. When this signal is triggered, all these functions are called.
Of course, you can target platforms on which the functions will be executed: the server (for Python code) or any set of browser windows.

```python
from df_websockets.decorators import everyone, signal

@signal(path="myproject.first_signal", is_allowed_to=everyone)
def my_first_signal(window_info, content=None):
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


```python
from df_websockets.tasks import WINDOW, trigger

```