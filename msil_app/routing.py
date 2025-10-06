from django.urls import re_path
from .consumers import ReportsConsumer,StartConsumer,OverviewConsumer

websocket_urlpatterns = [
    re_path(r"ws/reports/$", ReportsConsumer.as_asgi()),
    re_path(r"ws/start/$", StartConsumer.as_asgi()),
    re_path(r"ws/overview/$", OverviewConsumer.as_asgi()),

]
