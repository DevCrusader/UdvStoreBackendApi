from django.db.models import Q
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order, Customer
from .serializers import MyTokenObtainPairSerializer, OrderPureSerializer, OrderSerializer, OrderAdminSerializer, UserPublicInfoSerializer


# Create your views here.
class MyTokenObtainPairView(TokenObtainPairView):
    """Кастомный класс для токенов jwt"""
    serializer_class = MyTokenObtainPairSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_balance(request):
    return Response({"balance": request.user.customer.balance}, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    """Формирует заказ пользователя"""
    office_ = request.data.get("office")

    # Проверяет, что переданный оффис валидный
    if office_ is None or (office_ not in ["Mira", "Yasnaya", "Lenina"]):
        return Response({"error": "Not valid office address."}, status=400)

    payment_method = request.data.get('paymentMethod')

    # Проверяет, что переданный метод оплаты валидный
    if payment_method not in ["rubles", "ucoins"]:
        return Response({'error': "Not valid payment method."}, status=400)

    # Проверяет, что в корзине пользователя существуют item's
    if not len(request.user.productcart_set.all()):
        return Response({"error": "User's cart does not have any item."}, status=500)

    # Если метод оплаты - юкоины, то списывает деньги со счёта
    if payment_method == "ucoins":
        total_count = request.user.customer.cart_total_count()
        if total_count > request.user.customer.balance:
            return Response({"error": "Not enough ucoins"}, status=400)
        request.user.customer.decrease_balance(total_count)

    request.data["payment_method"] = payment_method
    request.data['user'] = request.user.id

    serializer = OrderPureSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        Order.objects.get(id=serializer.data.get("id")).set_product_list(request.user.customer.extract_cart())
        request.user.customer.clear_cart()
        return Response(serializer.data)
    return Response(serializer.errors, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_order(request, pk):
    """Метод возвращает определенный заказ по его ключу"""
    order = Order.objects.filter(id=pk)

    # Проверяет, существует ли искомый по ключу заказ
    if not order.exists():
        return Response({"error": "Desired order does not exist."}, status=400)

    return Response(OrderSerializer(order.first()).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_orders_admin(request):
    """Метод вовзращает список всех заказов в админ панель"""

    # Проверяет, достаточно ли у пользователя прав для данного действия
    if request.user.customer.role != "Administrator" and request.user.customer.role != "Moderator":
        return Response({"error": f"Not enough rights."}, status=403)

    return Response(OrderAdminSerializer(
        Order.objects.filter(~Q(user=request.user) & (Q(state="Accepted") | Q(state="Formed"))), many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_order_state(request, pk):
    """Метод меняет состояние заказа, по переданному ключу"""

    # Проверяет, достаточно ли у пользователя правд для данного действия
    if request.user.customer.role != "Administrator" and request.user.customer.role != "Moderator":
        return Response({"error": f"Not enough rights."}, status=403)

    order = Order.objects.filter(id=pk).first()

    # Проверяет, существует ли заказ по переданному запросу
    if order is None:
        return Response({"error": f"Desired order does not exist."}, status=400)

    state_ = request.GET.get("state")

    if state_ not in Order.OrderStateChoice.values:
        return Response({"error": "Incorrect new state"}, status=400)

    order.set_state(state_)
    return Response({"message": "Successfully"}, status=200)


@api_view(["GET"])
def user_search(request):
    search = request.GET.get("search")

    if search is None:
        return Response({"error": "Search request is empty."}, status=400)

    # search = list(map(lambda x: x[:5].capitalize(), search.strip().split(' ')))
    # customers = Customer.objects.all()[:3]

    return Response(UserPublicInfoSerializer(Customer.objects.all()[:3], many=True).data)
