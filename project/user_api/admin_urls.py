from django.urls import path

from .views import get_orders_admin, change_order_state, create_user, create_balance_changes, \
    delete_user, change_user_permission, order_cancellation

urlpatterns = [
    path("orders/", get_orders_admin),
    path("order/cancellation/", order_cancellation),
    path("order/<str:pk>/", change_order_state),
    path("balance-cahnges", create_balance_changes),
    path("user/", create_user),
    path("user/delete/<str:pk>/", delete_user),
    path("user/role/<str:pk>/", change_user_permission),
]
