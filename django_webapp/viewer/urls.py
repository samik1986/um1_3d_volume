from django.urls import path
from . import views
from . import dash_apps # Registers the Dash app

urlpatterns = [
    path('', views.index, name='index'),
    path('api/load', views.load_volume, name='load_volume'),
]
