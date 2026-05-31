"""
URL configuration for campus_ai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from core import views as core_views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


SWAGGER_SETTINGS = {

    'SECURITY_DEFINITIONS': {

        'Bearer': {

            'type': 'apiKey',

            'name': 'Authorization',

            'in': 'header',

            'description': """
            JWT Authorization header using the Bearer scheme.

            Example:
            Bearer eyJhbGciOiJIUzI1NiIs...
            """
        }
    }
}


schema_view = get_schema_view(

    openapi.Info(

        title="Smart Campus API",

        default_version='v1',

        description="""
        Enterprise Smart Campus Management Platform APIs
        """,
    ),

    public=True,

    permission_classes=[
        permissions.AllowAny,
    ],
)


urlpatterns = [

    path(
        "admin/attendance-monitoring/",
        core_views.admin_attendance_monitoring,
        name="admin_attendance_monitoring"
    ),

    path(
        "admin/operations-monitoring/",
        core_views.admin_operations_monitoring,
        name="admin_operations_monitoring"
    ),
    path('', include('django_prometheus.urls')),

    path(
        'admin/',
        admin.site.urls
    ),

    path("", include("core.urls")),   
    
    path(
        'accounts/',
        include('accounts.urls')
    ),

    path(
        'ml/',
        include('ml.urls')
    ),

    path(
        'attendance/',
        include('attendance.urls')
    ),

    path(
        "canteen/",
        include("canteen.urls")
    ),

    path(
        'notifications/',
        include('notifications.urls')
    ),

    path(
        "planner/",
        include("planner.urls")
    ),

    path(
        'api/token/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),

    path(
        'api/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    path(
        'swagger/',
        schema_view.with_ui(
            'swagger',
            cache_timeout=0
        ),
        name='schema-swagger-ui'
    ),

    path(
        'redoc/',
        schema_view.with_ui(
            'redoc',
            cache_timeout=0
        ),
        name='schema-redoc'
    ),
]


urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)

urlpatterns += static(
    settings.STATIC_URL,
    document_root=settings.STATIC_ROOT
)
