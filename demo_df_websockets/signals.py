from df_websockets.decorators import signal, everyone
from df_websockets.tasks import trigger, BROADCAST


@signal(path="demo.trigger_signals", is_allowed_to=everyone, queue="celery")
def my_first_signal(window_info):
    trigger(
        window_info,
        "html.after",
        to=BROADCAST,
        selector=".after",
        content="<li><i>New text</i></li>",
    )
    trigger(
        window_info,
        "html.before",
        to=BROADCAST,
        selector=".before",
        content="<li><i>New text</i></li>",
    )
    trigger(
        window_info,
        "html.append",
        to=BROADCAST,
        selector=".append",
        content="<span> <i>New text</i></span>",
    )
    trigger(
        window_info,
        "html.prepend",
        to=BROADCAST,
        selector=".prepend",
        content="<span> <i>New text</i> </span>",
    )
