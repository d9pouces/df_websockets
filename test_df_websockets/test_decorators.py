from django.test import TestCase

from df_websockets import ws_settings
from df_websockets.decorators import REGISTERED_SIGNALS, Connection, server_side, signal


def signal_valid_function(window_info, arg_1: str, arg_2: int = None):
    return arg_1, arg_2


def signal_invalid_function(arg):
    return arg


class TestDecorator(TestCase):
    def test_signal_valid(self):
        signal(signal_valid_function)
        signal_name = "test_df_websockets.test_decorators.signal_valid_function"
        self.assertTrue(signal_name in REGISTERED_SIGNALS)
        self.assertEqual(1, len(REGISTERED_SIGNALS[signal_name]))
        signal_obj: Connection = REGISTERED_SIGNALS[signal_name][0]
        self.assertEqual(signal_obj.function, signal_valid_function)
        self.assertEqual(signal_obj.path, signal_name)
        self.assertEqual(signal_obj.is_allowed_to, server_side)
        self.assertEqual(signal_obj.queue, ws_settings.WEBSOCKET_DEFAULT_QUEUE)
        self.assertEqual({"arg_1": str, "arg_2": int}, signal_obj.argument_types)
        self.assertEqual({"arg_1"}, signal_obj.required_arguments_names)
        self.assertEqual({"arg_2"}, signal_obj.optional_arguments_names)
        self.assertEqual({"arg_1", "arg_2"}, signal_obj.accepted_argument_names)

    def test_signal_invalid(self):
        self.assertRaises(ValueError, lambda: signal(signal_invalid_function))
