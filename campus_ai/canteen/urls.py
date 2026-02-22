from django.urls import path
from . import views

urlpatterns = [
    path("test/", views.test_recommendation, name="test_recommendation"),
    path("order/", views.place_order, name="place_order"),
    path("my-orders/", views.my_orders, name="my_orders"),
]
