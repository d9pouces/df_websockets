import json
from unittest import mock
from urllib.parse import quote_plus

from channels.layers import get_channel_layer
from channels.sessions import SessionMiddlewareStack
from channels.testing import WebsocketCommunicator
from django.core.cache.backends.locmem import LocMemCache
from django.http import HttpRequest, HttpResponse, parse_cookie
from django.test import TestCase, override_settings

from df_websockets import tasks, ws_settings
from df_websockets.consumers import DFConsumer, get_websocket_topics
from df_websockets.middleware import WebsocketMiddleware
from df_websockets.tasks import SERVER, WINDOW, _topic_serializer, set_websocket_topics
from df_websockets.utils import valid_topic_name
from df_websockets.window_info import WindowInfo


class TestGetWebsocketTopics(TestCase):
    def test_get_websocket_topics(self):
        window_info = WindowInfo()
        window_info.window_key = "test_key"
        with mock.patch(
            "django.core.cache.cache",
            new=LocMemCache("name", {}),
        ):
            set_websocket_topics(window_info, "test", 100)
            actual = get_websocket_topics(window_info)
            expected = {
                "fea736b153fc5c81b4d5002610f6c8374a5677cdce3b72245a4c32db5740c8f0",
                "7e8c980efe5bc654f4eae9b110014bcb3cb1a892a0eb70092abec016072eeb2d",
                "fee2382dc609c3d54f5b0295507e8f85d52c0ba3e4f64ff8cabf373331efb7bd",
                "f6728284c836a3ebc25a6dc85847b147961a0934d10e2950c3e8f92936f10865",
            }
            self.assertEqual(
                expected,
                set(actual),
            )


class TestDFConsumer(TestCase):
    async def test_websocket_consumer(self):
        """Tests that WebsocketConsumer is implemented correctly."""
        signal_calls = []
        request = HttpRequest()
        response = HttpResponse()
        app = DFConsumer()
        domain, port = "example.com", 8000
        ws_url = ws_settings.WEBSOCKET_URL
        q_url = quote_plus("ws://%s:%s%s" % (domain, port, ws_url))
        request.META = {"SERVER_NAME": domain, "SERVER_PORT": str(port)}

        def trigger_signal(*args, **kwargs):
            signal_calls.append((args, kwargs))

        with self.settings(
            ALLOWED_HOSTS=[domain, "%s:%s" % (domain, port)],
            CSRF_COOKIE_DOMAIN=domain,
        ):
            with mock.patch(
                "df_websockets.tasks._trigger_signal",
                new=trigger_signal,
            ):
                cls = WebsocketMiddleware(lambda _: HttpResponse())
                cls.process_request(request)
                test_topic = "topic"
                set_websocket_topics(request, test_topic)
                cls.process_response(request, response)
                # noinspection PyUnresolvedReferences
                cookie = "dfwskey=%s;dfwsurl=%s" % (request.window_key, q_url)
                headers = [
                    ("Origin", "http://%s:%s" % (domain, port)),
                    ("Pragma", "no-cache"),
                    ("Sec-WebSocket-Key", "aMBKe/rXeKzfFSxjljqmdw=="),
                    ("Sec-WebSocket-Version", "13"),
                    ("Upgrade", "websocket"),
                    ("Sec-WebSocket-Extensions", "permessage-deflate"),
                    ("User-Agent", "Mozilla/5.0 (KHTML, like Gecko)"),
                    ("Cache-Control", "no-cache"),
                    ("Connection", "Upgrade"),
                    ("Cookie", cookie),
                ]
                headers = [(x.encode(), y.encode()) for (x, y) in headers]

                # Test a normal connection
                communicator = WebsocketCommunicator(app, ws_url, headers=headers)
                communicator.scope["server"] = (domain, 8000)
                communicator.scope["cookies"] = parse_cookie(cookie)
                connected, _ = await communicator.connect()

                self.assertTrue(connected)
                self.assertEqual(3, len(app.topics))
                self.assertTrue(valid_topic_name("-broadcast") in app.topics)
                # noinspection PyUnresolvedReferences
                self.assertEqual(app.window_info.window_key, request.window_key)

                await tasks._trigger_signal_async(
                    app.window_info, "test.test_ws", to=WINDOW, kwargs={"1": "2"}
                )
                ws_msg = json.loads(await communicator.receive_from())
                self.assertTrue("signal_id" in ws_msg)
                del ws_msg["signal_id"]
                self.assertEqual(
                    {"signal": "test.test_ws", "opts": {"1": "2"}},
                    ws_msg,
                )

                app.receive(json.dumps({"signal": "test.test_server", "opts": {}}))
                self.assertEqual(1, len(signal_calls))
                self.assertEqual(
                    (app.window_info, "test.test_server"), signal_calls[0][0]
                )
                self.assertEqual(
                    {
                        "to": [SERVER],
                        "kwargs": {},
                        "from_client": True,
                        "eta": None,
                        "expires": None,
                        "countdown": None,
                    },
                    signal_calls[0][1],
                )

                await tasks._call_ws_signal(
                    "test.test_ws",
                    "42",
                    [_topic_serializer(app.window_info, test_topic)],
                    {"1": "3"},
                )
                ws_msg = await communicator.receive_from()
                self.assertEqual(
                    {"signal": "test.test_ws", "opts": {"1": "3"}, "signal_id": "42"},
                    json.loads(ws_msg),
                )
                await communicator.disconnect()
