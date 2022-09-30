from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import MyTokenObtainPairView, create_order, get_order, get_balance, user_search


urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view()),
    path('token/', MyTokenObtainPairView.as_view()),
    path("balance/", get_balance),
    path('order/create/', create_order),
    path('order/<str:pk>/', get_order),
    path('search/', user_search),
]
