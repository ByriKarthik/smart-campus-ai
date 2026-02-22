from django.urls import path

from . import views


urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-resources/", views.admin_resources, name="admin_resources"),
    path("faculty-dashboard/", views.faculty_dashboard, name="faculty_dashboard"),
    path("faculty-timetable/", views.faculty_timetable_view, name="faculty_timetable"),
    path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student-timetable/", views.student_timetable_view, name="student_timetable"),
]
