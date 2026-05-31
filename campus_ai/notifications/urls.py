from django.urls import path

from .views import trigger_alert


urlpatterns = [

    path(
        'trigger-alert/',
        trigger_alert
    ),
]