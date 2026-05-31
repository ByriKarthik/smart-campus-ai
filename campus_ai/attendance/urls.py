from django.urls import path
from .views import mark_attendance, auto_detect_attendance, student_attendance_api

urlpatterns = [
    path('mark/', mark_attendance, name='mark_attendance'),
    path('auto-detect/', auto_detect_attendance, name='auto_detect_attendance'),
    path('api/student-attendance/<str:student_id>/', student_attendance_api, name='student_attendance_api'),
]
