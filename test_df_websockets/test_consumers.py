from unittest import mock

from df_websockets import ws_settings
from df_websockets.window_info import WindowInfo

from df_websockets.consumers import get_websocket_topics
from django.test import TestCase


class FakeConnection:
    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def lrange(self, key, start, end):
        if key == "%stest_key" % ws_settings.WEBSOCKET_REDIS_PREFIX:
            return ["a", "b"]
        return []


class TestGetWebsocketTopics(TestCase):
    def test_get_websocket_topics(self):
        window_info = WindowInfo()
        window_info.window_key = "test_key"
        with mock.patch(
                "df_websockets.tasks.get_websocket_redis_connection",
                side_effect=lambda: FakeConnection(),
        ):
            topics = get_websocket_topics(window_info)
            self.assertEqual(['ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb',
                              '3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d'], topics)
