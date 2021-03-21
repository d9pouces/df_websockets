from django.template.response import TemplateResponse

from df_websockets.tasks import set_websocket_topics


def index(request):
    set_websocket_topics(request)
    return TemplateResponse(request, "index.html")
