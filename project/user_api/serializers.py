from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Order, Customer, User, BalanceReplenish


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['balance'] = user.customer.balance
        token['role'] = user.customer.role

        return token


class OrderPureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'products', 'payment_method', 'office')


class OrderAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'products', 'state', 'created_date', 'office', 'user_name', "payment_method")


class UserPublicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('user_id', 'name', 'balance', 'role')


class UserPureSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class CustomerPureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class BalanceReplenishPureSerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceReplenish
        fields = "__all__"
