from django.test import TestCase

from df_websockets.decorators import signal
from df_websockets.tasks import SERVER, WINDOW, trigger
from df_websockets.testing import SignalQueue
from df_websockets.window_info import WindowInfo


# noinspection PyUnusedLocal
@signal(path="test.signal", queue="test-queue")
def test_fn(window_info: WindowInfo, arg_1=None):
    pass


class TestSignalQueue(TestCase):
    def test_signal_queue(self):
        window_info = WindowInfo()
        window_info.window_key = "7f8d28ba4820"
        with SignalQueue() as sq:
            trigger(
                window_info,
                "test.signal",
                to=[SERVER, WINDOW],
                arg_1="test",
            )
        self.assertEqual(
            {"-window.7f8d28ba4820": [("test.signal", {"arg_1": "test"})]},
            sq.ws_signals,
        )
        self.assertEqual(
            {
                "test-queue": [
                    [
                        "test.signal",
                        {
                            "window_key": "7f8d28ba4820",
                            "user_pk": None,
                            "username": None,
                            "is_superuser": False,
                            "is_staff": False,
                            "is_active": False,
                            "csrf_cookie": "",
                            "perms": None,
                            "user_agent": "",
                            "user_set": False,
                            "language_code": None,
                        },
                        {"arg_1": "test"},
                        False,
                        [],
                        True,
                        "test-queue",
                    ]
                ]
            },
            sq.python_signals,
        )
