from django.db.models import Q
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order, Customer, User
from .serializers import MyTokenObtainPairSerializer, OrderPureSerializer, \
    OrderSerializer, OrderAdminSerializer, UserPublicInfoSerializer, UserPureSerializer, CustomerPureSerializer, \
    BalanceReplenishPureSerializer


# Create your views here.
class MyTokenObtainPairView(TokenObtainPairView):
    """Кастомный класс для токенов jwt"""
    serializer_class = MyTokenObtainPairSerializer


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
    return Response({"state": order.state}, status=200)


@api_view(["GET"])
def user_search(request):
    """
    Поиск пользователей по запросу
    """
    search = request.GET.get("search")

    if search is None:
        return Response([], status=200)

    search = search.split(" ")

    if len(search) != 3:
        return Response({"error": "Incorrect search, it must include 3 fields, "
                                  "put '*' on unknown field."}, status=400)

    ln, fn, p = search

    customers = Customer.objects.filter(
        Q(last_name__startswith=ln[:6] if ln != "*" else "")
        & Q(first_name__startswith=fn[:6] if fn != "*" else "")
        & Q(patronymic__startswith=p[:6] if p != "*" else "")
    ).order_by("last_name" if ln != "*" else "first_name" if fn != "*" else "patronymic")

    return Response(UserPublicInfoSerializer(customers, many=True).data)


@api_view(['GET'])
def role_users(request):
    """
    Получить список пользователей определенной роли
    """

    # Получаем роль из GET ззапроса
    role = request.GET.get('role')

    # Если таковая отсутствует, то отсылаем 400
    if role is None:
        return Response({"error": "Request does not contain role param."}, status=400)

    # Преобразуем к приемлемому виду
    role = role.capitalize()

    # Если переданная роль не совпадает с данными, то отслыаем 400
    if role not in Customer.RoleChoice.values:
        return Response({"error": "Requested role does not exist."}, status=400)

    return Response(UserPublicInfoSerializer(Customer.objects.filter(role=role), many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_user(request):
    """
    Метод создаёт нового пользователя, должны быть переданы все параметры
    """

    # Check requested user role
    if request.user.customer.role != "Administrator" and request.user.customer.role != "Moderator":
        return Response({"error": "Not enough permissions."}, status=403)

    # Check that the request contain all fields
    missing_fields = []
    for field in ["lastName", "firstName", "patronymic", "balance", "role"]:
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
    role = request.data.get('role')

    if request.user.customer.role != "Administrator" and role != "Employee":
        return Response({"error": "Only the service administrator can "
                                  "appoint other users as moderators or higher."}, status=403)

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
            "role": role
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
def create_balance_replenishment(request):
    # Check requested user_id permission
    if not (request.user.customer.check_moderator_role() or request.user.customer.check_admin_role()):
        return Response({"error": "Not enough permissions."}, status=403)

    comment = request.data.get("comment")
    count = request.data.get("count")
    user_id = request.data.get("userId")

    # Comment fields validation
    if comment is None or not comment:
        return Response({"error": "Invalid field: comment."}, status=400)

    # Count fields validation
    if count is None or not count.isdigit():
        return Response({"error": "Invalid field: count."}, status=400)

    # UserId fields validation
    if not User.objects.filter(id=user_id).first():
        return Response({"error": "Desired user_id does not exist."}, status=400)

    if request.user.id == user_id:
        return Response({"error": "You can't replenish your own balance."}, status=400)

    # Create seriazlizer
    serializer = BalanceReplenishPureSerializer(data={
        "user": user_id,
        "admin_id": request.user.id,
        "comment": comment,
        "count": count
    })

    if serializer.is_valid():
        br = serializer.save()
        return Response(BalanceReplenishPureSerializer(br, many=False).data, status=200)

    # Response 500 if there some errors with balance replenishment serializer
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

    user = User.objects.filter(id=pk).first()

    # Check that desired user exists
    if user is None:
        return Response({"error": "Desired user does not exist."}, status=400)

    admin_perms = request.user.customer.check_admin_role()
    moderator_perms = request.user.customer.check_moderator_role()

    # Check permissions
    if not (admin_perms or moderator_perms):
        return Response({"error": "Not enough permissions."}, status=403)

    # Check permissions level
    if moderator_perms and user.customer.role != "Employee":
        return Response({"error": "You can't delete administrators or moderators."}, status=400)

    customer = {
        "user_id": None,
        "name": user.customer.name(),
        "balance": user.customer.balance,
        "role": user.customer.role,
        "first_name": user.customer.first_name,
        "last_name": user.customer.last_name,
        "patronymic": user.customer.patronymic
    }

    user.delete()
    return Response(customer, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def manage_user_role(request, pk):
    """
    Метод меняет роль пользователя на данную
    """
    user = User.objects.filter(id=pk).first()

    if user is None:
        return Response({"error": "Desired user does not exist."}, status=400)

    if not request.user.customer.check_admin_role():
        return Response({"error": "Only administrator can change user role."}, status=400)

    role = request.data.get("role")

    if role is None or role not in Customer.RoleChoice.values:
        return Response({"error": "Invalid requested role."}, status=400)

    user.customer.set_role(role)
    return Response(UserPublicInfoSerializer(user.customer, many=False).data, status=200)
