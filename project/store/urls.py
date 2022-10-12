from django.urls import path
from .views import get_products, get_product, get_cart, manage_cart, add_cart, get_product_test


urlpatterns = [
    path('products/', get_products),
    path('products/<str:pk>/', get_product),
    path('cart/', get_cart),
    path('cart/add/', add_cart),
    path('cart/<str:pk>/', manage_cart),
    path("test/", get_product_test)
]
