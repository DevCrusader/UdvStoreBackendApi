from django.db.models import Q
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order, Customer, User, SecretWord
from .serializers import MyTokenObtainPairSerializer, OrderPureSerializer, \
    OrderSerializer, OrderAdminSerializer, UserPublicInfoSerializer, UserPureSerializer, CustomerPureSerializer, \
    BalanceWriteOffPureSerializer, BalanceReplenishPureSerializer


# Create your views here.
class MyTokenObtainPairView(TokenObtainPairView):
    """Кастомный класс для токенов jwt"""
    serializer_class = MyTokenObtainPairSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    """Формирует заказ пользователя"""
    office_ = request.data.get("office")

    # Check office
    if office_ is None:
        return Response({"error": "Office is none."}, status=400)

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
        serializer = BalanceWriteOffPureSerializer(data={
            "user": request.user.id,
            "admin_id": request.user.id,
            "comment": "Покупка мерча",
            "count": total_count
        })

        if serializer.is_valid():
            serializer.save()

    request.data["payment_method"] = payment_method
    request.data['user'] = request.user.id

    serializer = OrderPureSerializer(data=request.data)

    if serializer.is_valid():
        order = serializer.save()
        order.set_product_list(request.user.customer.extract_cart())
        request.user.customer.clear_cart()
        return Response(OrderSerializer(order, many=False).data)
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
    if not request.user.customer.admin_permissions:
        return Response({"error": f"Not enough rights."}, status=403)

    return Response(OrderAdminSerializer(
        Order.objects.filter(state="Accepted"), many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_order_state(request, pk):
    """Метод меняет состояние заказа, по переданному ключу"""

    # Проверяет, достаточно ли у пользователя правд для данного действия
    if not request.user.customer.admin_permissions:
        return Response({"error": f"Not enough rights."}, status=403)

    order = Order.objects.filter(id=pk).first()

    # Проверяет, существует ли заказ по переданному запросу
    if order is None:
        return Response({"error": f"Desired order does not exist."}, status=400)

    state = request.data.get("state")

    if state not in Order.OrderStateChoice.values:
        return Response({"error": "Incorrect new state"}, status=400)

    order.set_state(state)
    return Response(OrderAdminSerializer(order).data, status=200)


@api_view(["GET"])
def user_search(request):
    """
    Поиск пользователей по запросу
    """
    fn = request.GET.get("firstName")
    ln = request.GET.get("lastName")
    p = request.GET.get("patronymic")

    if fn is None or ln is None or p is None:
        return Response({"error": "Some of requested parameters is None."}, status=400)

    customers = Customer.objects.filter(
        Q(last_name__startswith=ln[:6] if ln != "*" else "")
        & Q(first_name__startswith=fn[:6] if fn != "*" else "")
        & Q(patronymic__startswith=p[:6] if p != "*" else "")
    ).order_by("last_name" if ln != "*" else "first_name" if fn != "*" else "patronymic")

    return Response(UserPublicInfoSerializer(customers, many=True).data)


@api_view(['GET'])
def get_admins(request):
    """
    Получить список пользователей определенной роли
    """
    return Response(UserPublicInfoSerializer(
        Customer.objects.filter(admin_permissions=True), many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_user(request):
    """
    Метод создаёт нового пользователя, должны быть переданы все параметры
    """

    # Check requested user role
    if not request.user.customer.admin_permissions:
        return Response({"error": "Not enough permissions."}, status=403)

    # Check that the request contain all fields
    missing_fields = []
    for field in ["lastName", "firstName", "patronymic", "balance", "permission"]:
        if request.data.get(field) is None:
            missing_fields.append(field)

    # Response error if some field is missing
    if missing_fields:
        return Response({"error": f"The request does not contain fields: {', '.join(missing_fields)}"}, status=400)

    # Get fields from request
    last_name = request.data.get('lastName').strip()
    first_name = request.data.get('firstName').strip()
    patronymic = request.data.get('patronymic').strip()

    try:
        Customer.objects.get(first_name=first_name, last_name=last_name, patronymic=patronymic)
        return Response({"error": "User with requested params already exists. "
                                  "If you still want to register, try to change some param."}, status=400)
    except Customer.DoesNotExist:
        pass

    balance = request.data.get('balance')
    permission = request.data.get('permission')

    # Create User Serializer
    username = "_".join([last_name, first_name, patronymic])

    user_serializer = UserPureSerializer(data={
        'username': username,
        'password': username
    })

    if user_serializer.is_valid():
        user = user_serializer.save()

        # Create Customer Serializer
        customer_serializer = CustomerPureSerializer(data={
            "user": user.id,
            "first_name": first_name,
            "last_name": last_name,
            "patronymic": patronymic,
            "balance": balance,
            "admin_permissions": permission
        })

        if customer_serializer.is_valid():
            customer = customer_serializer.save()
            return Response(UserPublicInfoSerializer(customer, many=False).data)

        # Response 500 if there are some error in customer serializer
        return Response(customer_serializer.errors, status=500)

    # Response 500 if there are some error in user serializer
    return Response(user_serializer.errors, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_balance_changes(request):
    # Check requested user_id permission
    if not request.user.customer.admin_permissions:
        return Response({"error": "Not enough permissions."}, status=403)

    new_balance = request.data.get("newBalance")
    comment = request.data.get("comment")
    user_id = request.data.get("userId")

    # NewBalance field validation
    if new_balance is None or not new_balance.isdigit() or int(new_balance) < 0:
        return Response({"error": "NewBalance parameter is missing."}, status=400)

    new_balance = int(new_balance)

    # Comment field validation
    if comment is None or not comment:
        return Response({"error": "Invalid field: comment."}, status=400)

    user = User.objects.filter(id=user_id).first()

    # UserId field validation
    if not user:
        return Response({"error": "Desired user_id does not exist."}, status=400)

    if new_balance == user.customer.balance:
        return Response({"error": "The user already has requested balance. "
                                  "Probably another administrator changed the balance for this reason."}, status=400)

    # Balance change serializer data
    data = {
        "user": user_id,
        "admin_id": request.user.id,
        "comment": comment,
        "count": abs(user.customer.balance - new_balance)
    }

    # Create balance change serializer based on change type
    serializer = BalanceReplenishPureSerializer(data=data) \
        if new_balance > user.customer.balance else \
        BalanceWriteOffPureSerializer(data=data)

    if serializer.is_valid():
        data = serializer.save()
        # Return updated customer object
        return Response(UserPublicInfoSerializer(data.user.customer, many=False).data)

    # Return 500 in case serializer with errors
    return Response(serializer.errors, status=500)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_user(request, pk):
    """
    Метод позволяет удалить некоторого пользователя
    """

    if pk is None or not pk.isdigit():
        return Response({"error": "User id must be integer field."}, status=400)

    # Case when user delete himself
    if request.user.id == int(pk):
        return Response({"error": "You can't delete your own account."}, status=400)

    if not request.user.customer.admin_permissions:
        return Response({"error": "Not enough permissions."}, status=403)

    user = User.objects.filter(id=pk).first()

    # Check that desired user exists
    if user is None:
        return Response({"error": "Desired user does not exist."}, status=400)

    customer = {
        "user_id": None,
        "name": user.customer.name(),
        "balance": user.customer.balance,
        "admin_permissions": user.customer.admin_permissions,
        "first_name": user.customer.first_name,
        "last_name": user.customer.last_name,
        "patronymic": user.customer.patronymic
    }

    user.delete()
    return Response(customer, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_user_permission(request, pk):
    """
    Метод меняет роль пользователя на данную
    """
    user = User.objects.filter(id=pk).first()

    if user is None:
        return Response({"error": "Desired user does not exist."}, status=400)

    if not request.user.customer.admin_permissions:
        return Response({"error": "Only administrator can change user role."}, status=400)

    if user.id == request.user.id:
        return Response({"error": "You can't change your own role."}, status=400)

    if user.customer.admin_permissions:
        user.customer.remove_admin_permissions()
    else:
        user.customer.grant_admin_permissions()

    return Response(UserPublicInfoSerializer(user.customer, many=False).data, status=200)


@api_view(["POST"])
def self_register_user(request):
    missing_fields = []
    for field in ["firstName", "lastName", "patronymic", "secretWord"]:
        if request.data.get(field) is None:
            missing_fields.append(field)

    if len(missing_fields) != 0:
        return Response({"error": f"These parameters are missing: {' '.join(missing_fields)}."}, status=400)

    first_name = request.data.get("firstName")
    last_name = request.data.get("lastName")
    patronymic = request.data.get("patronymic")
    secret_word = request.data.get("secretWord")

    if not SecretWord.objects.first().check_secret_word(secret_word):
        return Response({"error": "Incorrect secret word."}, status=400)

    customer = Customer.objects.filter(first_name=first_name, last_name=last_name, patronymic=patronymic)

    if customer.exists():
        return Response(
            {"error": f"Customer {' '.join([last_name, first_name, patronymic])} already exists."},
            status=400)

    username = "_".join([last_name, first_name, patronymic])
    user_serializer = UserPureSerializer(data={
        "username": username,
        "password": username
    })

    if user_serializer.is_valid():
        user = user_serializer.save()

        customer_serializer = CustomerPureSerializer(data={
            "user": user.id,
            "first_name": first_name,
            "last_name": last_name,
            "patronymic": patronymic,
            "balance": 0,
            "admin_permissions": False
        })

        if customer_serializer.is_valid():
            customer = customer_serializer.save()
            return Response(UserPublicInfoSerializer(customer, many=False).data)

        return Response(customer_serializer.errors, status=500)

    return Response(user_serializer.errors, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def order_cancellation(request):
    if not request.user.customer.admin_permissions:
        return Response({"error": "Not enough permissions."}, status=403)

    order_id = request.data.get("orderId")

    if order_id is None:
        return Response({"error": "OrderId parameter is missing."}, status=400)

    order = Order.objects.filter(id=order_id).first()

    if order is None:
        return Response({"error": "Desired order does not exists."}, status=400)

    total_count = sum([item["count"] * item["price"] for item in order.products()])

    serializer = BalanceReplenishPureSerializer(data={
        "user": order.user.id,
        "admin_id": request.user.id,
        "comment": f"Возврат средств из-за отмены заказа #{order_id}",
        "count": total_count
    })

    if serializer.is_valid():
        serializer.save()
        order.delete()
        return Response(OrderAdminSerializer(order).data)

    return Response(serializer.errors, status=500)
