from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import MyTokenObtainPairView, create_order, get_order, user_search, get_admins, self_register_user


urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view()),
    path('token/', MyTokenObtainPairView.as_view()),
    path('order/create/', create_order),
    path('order/<str:pk>/', get_order),
    path('admins/', get_admins),

    path('search', user_search),
    path('self-register/', self_register_user),
]
