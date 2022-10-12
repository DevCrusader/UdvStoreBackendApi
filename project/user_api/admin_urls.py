from django.urls import path

from .views import get_orders_admin, change_order_state, create_user, create_balance_replenishment, \
    delete_user, manage_user_role

urlpatterns = [
    path("orders/", get_orders_admin),
    path("order/<str:pk>/", change_order_state),
    path("balance-replenishment/", create_balance_replenishment),
    path("user/", create_user),
    path("user/delete/<str:pk>/", delete_user),
    path("user/role/<str:pk>/", manage_user_role),
]
