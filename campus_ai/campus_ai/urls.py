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
from core import views as core_views

urlpatterns = [
    path("admin/attendance-monitoring/", core_views.admin_attendance_monitoring, name="admin_attendance_monitoring"),
    path("admin/operations-monitoring/", core_views.admin_operations_monitoring, name="admin_operations_monitoring"),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('ml.urls')),
    path('attendance/', include('attendance.urls')),
    path("canteen/", include("canteen.urls")),
    path("planner/", include("planner.urls")),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
