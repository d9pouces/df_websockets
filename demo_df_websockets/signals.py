from django.conf import settings
from django.utils.translation import gettext_lazy as _

from df_websockets.decorators import everyone, signal
from df_websockets.tasks import BROADCAST, trigger


@signal(path="demo.html.after", is_allowed_to=everyone)
def demo_html_after(window_info):
    new_text = str(_("Lookup"))
    trigger(
        window_info,
        "html.after",
        to=BROADCAST,
        selector=".after",
        content=f'<li class="list-group-item"><i>{new_text}</i></li>',
    )


@signal(path="demo.html.append", is_allowed_to=everyone)
def demo_html_append(window_info):
    trigger(
        window_info,
        "html.append",
        to=BROADCAST,
        selector=".append",
        content="<span> <i>New text</i></span>",
    )


@signal(path="demo.html.prepend", is_allowed_to=everyone)
def demo_html_prepend(window_info):
    trigger(
        window_info,
        "html.prepend",
        to=BROADCAST,
        selector=".prepend",
        content="<span> <i>New text</i> </span>",
    )


@signal(path="demo.html.before", is_allowed_to=everyone)
def demo_html_before(window_info):
    trigger(
        window_info,
        "html.before",
        to=BROADCAST,
        selector=".before",
        content='<li class="list-group-item"><i>New text</i></li>',
    )


@signal(path="demo.html.content", is_allowed_to=everyone)
def demo_html_content(window_info):
    trigger(
        window_info,
        "html.content",
        to=BROADCAST,
        selector=".content",
        content="<span> <i>New text</i> </span>",
    )


@signal(path="demo.html.replace_with", is_allowed_to=everyone)
def demo_html_replace_with(window_info):
    trigger(
        window_info,
        "html.replace_with",
        to=BROADCAST,
        selector=".replace_with .original",
        content="<span> <i>New text</i> </span>",
    )


@signal(path="demo.html.empty", is_allowed_to=everyone)
def demo_html_empty(window_info):
    trigger(
        window_info,
        "html.empty",
        to=BROADCAST,
        selector=".empty",
    )


@signal(path="demo.html.remove", is_allowed_to=everyone)
def demo_html_remove(window_info):
    trigger(
        window_info,
        "html.remove",
        to=BROADCAST,
        selector=".remove",
    )


@signal(path="demo.html.add_class", is_allowed_to=everyone)
def demo_html_add_class(window_info):
    trigger(
        window_info,
        "html.add_class",
        to=BROADCAST,
        selector=".add_class",
        class_name="text-success",
    )


@signal(path="demo.html.remove_class", is_allowed_to=everyone)
def demo_html_remove_class(window_info):
    trigger(
        window_info,
        "html.remove_class",
        to=BROADCAST,
        selector=".remove_class",
        class_name="text-danger",
    )


@signal(path="demo.html.remove_attr", is_allowed_to=everyone)
def demo_html_remove_attr(window_info):
    trigger(
        window_info,
        "html.remove_attr",
        to=BROADCAST,
        selector=".remove_attr input",
        attr_name="checked",
    )


@signal(path="demo.html.add_attribute", is_allowed_to=everyone)
def demo_html_add_attribute(window_info):
    trigger(
        window_info,
        "html.add_attribute",
        to=BROADCAST,
        selector=".add_attribute input",
        attr_name="checked",
        attr_value="checked",
    )


@signal(path="demo.html.boolean_attribute", is_allowed_to=everyone)
def demo_html_boolean_attribute(window_info):
    trigger(
        window_info,
        "html.boolean_attribute",
        to=BROADCAST,
        selector=".boolean_attribute .true input",
        name="checked",
        value=True,
    )
    trigger(
        window_info,
        "html.boolean_attribute",
        to=BROADCAST,
        selector=".boolean_attribute .false input",
        name="checked",
        value=False,
    )


@signal(path="demo.html.text", is_allowed_to=everyone)
def demo_html_text(window_info):
    trigger(
        window_info,
        "html.text",
        to=BROADCAST,
        selector=".text .original",
        content="<span>New text (HTML tags are not interpreted)</span>",
    )


@signal(path="demo.html.download_file", is_allowed_to=everyone)
def demo_html_download_file(window_info):
    trigger(
        window_info,
        "html.download_file",
        to=BROADCAST,
        url="%s%s" % (settings.STATIC_URL, "image.png"),
        filename="django.png",
    )


@signal(path="demo.html.focus", is_allowed_to=everyone)
def demo_html_focus(window_info):
    trigger(
        window_info,
        "html.focus",
        to=BROADCAST,
        selector=".focus",
    )


@signal(path="demo.html.forms.set", is_allowed_to=everyone)
def demo_html_forms_set(window_info):
    trigger(
        window_info,
        "html.forms.set",
        to=BROADCAST,
        selector=".forms-set",
        values=[
            {"name": "textarea", "value": "A textarea value"},
            {"name": "radio", "value": "3"},
            {"name": "checkbox", "value": ["3"]},
            {"name": "single-checkbox", "value": True},
            {"name": "no-single-checkbox", "value": False},
            {"name": "simple", "value": "lemon"},
            {"name": "groups", "value": "potato"},
            {"name": "multi", "value": ["lemon", "eggplant"]},
        ],
    )


# noinspection PyUnusedLocal
@signal(path="demo.exceptions.server", is_allowed_to=everyone)
def demo_exceptions_server(window_info):
    # noinspection PyStatementEffect
    1 / 0
