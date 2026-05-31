from django.urls import path

from .views import student_list_api, custom_token_obtain_view


urlpatterns = [

    path(
        'api/students/',
        student_list_api,
        name='student_list_api'
    ),

    path(
        'api/custom-token/',
        custom_token_obtain_view,
        name='custom_token'
    ),
]