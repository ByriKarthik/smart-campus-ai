from django.urls import path
from . import views

urlpatterns = [
    path('face-enroll/<str:user_id>/', views.face_enroll, name='face_enroll'),
]
