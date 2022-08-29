from django.http import HttpRequest
from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.utils.translation import activate, get_language, gettext
from django.utils.translation import gettext_lazy as _


class TestRenderToString(SimpleTestCase):
    def test_render_to_string(self):
        def welcome_translated(language):
            cur_language = get_language()
            try:
                activate(language)
                text = gettext("Lookup")
            finally:
                activate(cur_language)
            return text

        s = welcome_translated("fr")

        tpl_name = "admin/date_hierarchy.html"
        context = {
            "show": True,
            "choices": [],
            "back": {"title": _("Lookup"), "link": "/"},
        }
        request = HttpRequest()
        request.META = []
        activate("fr")
        s = render_to_string(tpl_name, context=context)
        self.assertTrue("Recherche" in s)
