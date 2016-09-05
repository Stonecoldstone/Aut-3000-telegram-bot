from django.conf.urls import url
from . import views

app_name = 'stickerbot'
urlpatterns = [
    url(r'^$', views.Bot.as_view(), name='bot'),
]