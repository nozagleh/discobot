from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    url('<string:client_id>/start/', views.start, name='start'),
    url('', views.index, name='index')
]