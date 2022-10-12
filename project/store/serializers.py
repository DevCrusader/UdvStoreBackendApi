from rest_framework import serializers
from .models import Product, ProductItem, ProductCart


class ProductPureSerializer(serializers.ModelSerializer):
    """Сериалазер для стандратной модели товара"""
    class Meta:
        model = Product
        fields = '__all__'


class ProductCartPureSerializer(serializers.ModelSerializer):
    """Сериалайзер для стандартной модели позиции корзины"""
    class Meta:
        model = ProductCart
        fields = "__all__"


class ProductStoreSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения простой информации о типе товара
    для вывода карточек на странице магазина"""
    class Meta:
        model = ProductItem
        fields = ('id', 'product_id', 'name', 'price', 'type', 'photo')


class ProductPageSerializer(serializers.ModelSerializer):
    """Сериалайзер для вывода подробной информации о товаре
    со всеми зависимыми типами товаров"""
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'description', 'have_size', 'items_list', )


class CartStoreSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения информации о товара в корзине
    со всеми зависимыми полями"""
    class Meta:
        model = ProductCart
        fields = ('id', 'product_id', 'name', 'type', 'theme',
                  'item_size', 'photo', 'count', 'price')


class ProductSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'photo_list')
