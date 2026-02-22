from django.urls import path

from . import views


urlpatterns = [
    path("schedule-remedial/", views.schedule_remedial, name="schedule_remedial"),
    path("join-remedial/", views.join_remedial, name="join_remedial"),
]

