from unittest import mock

from django.core.cache.backends.locmem import LocMemCache

from df_websockets import ws_settings
from df_websockets.tasks import set_websocket_topics
from df_websockets.window_info import WindowInfo

from df_websockets.consumers import get_websocket_topics
from django.test import TestCase


class TestGetWebsocketTopics(TestCase):
    def test_get_websocket_topics(self):
        window_info = WindowInfo()
        window_info.window_key = "test_key"
        with mock.patch(
            "django.core.cache.cache", new=LocMemCache("name", {}),
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
                expected, set(actual),
            )
