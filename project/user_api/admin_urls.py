from django.urls import path

from .views import get_orders_admin, change_order_state

urlpatterns = [
    path("orders/", get_orders_admin),
    path("order/<str:pk>/", change_order_state)
]
