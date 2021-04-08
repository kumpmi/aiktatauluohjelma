
from django.urls import path
from django.views import generic
from . import views

app_name = 'polls'
urlpatterns = [
    path('', views.IndexView, name='main'),
]
