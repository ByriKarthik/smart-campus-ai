from django.urls import path
from .views import mark_attendance, auto_detect_attendance

urlpatterns = [
    path('mark/', mark_attendance, name='mark_attendance'),
    path('auto-detect/', auto_detect_attendance, name='auto_detect_attendance'),
]
