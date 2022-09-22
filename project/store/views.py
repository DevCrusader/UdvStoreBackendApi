from django.core.exceptions import FieldError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import ProductStoreSerializer, CartStoreSerializer, ProductPageSerializer, ProductCartPureSerializer

from .models import Product, ProductItem


@api_view(["GET"])
def get_products(request):
    """Метод выдаёт товары в магазин
    По дефолту упорядочивается по дате создания товаров
    filter - принимает значения name или price
    order - принимает значениея desc или asc"""
    theme_ = request.GET.get('theme')

    if theme_ != "Udv" and theme_ != "Ussc":
        return Response({'error': f"Not valid theme"}, status=400)

    products = ProductItem.objects.filter(product__theme=theme_, state="actual")

    filter_ = request.GET.get('filter', None)
    order_ = request.GET.get('order', None)

    if filter_:
        try:
            products = products.order_by(f"{'-' if order_ == 'desc' else ''}product__{filter_}")
        except FieldError:
            pass

    return Response(ProductStoreSerializer(products, many=True).data)


@api_view(["GET"])
def get_product(request, pk):
    """Метод возвращает всю необходимую информацию о товаре:
    ID, название, цена, описание и список всех связанных с ним типов товара"""
    product = Product.objects.filter(id=pk).first()
    theme_ = request.GET.get("theme")

    if product is None:
        return Response({"error": f"Product with id {pk} does not exist."}, status=404)

    if theme_ != product.theme:
        return Response(
            {
                "error": "Product belongs to another theme, try with another theme.",
                "theme": product.theme
            }, status=400)

    return Response(ProductPageSerializer(product, many=False).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    """Метод возвращает необходимую информацию о товарах в корзине пользователя"""
    return Response(CartStoreSerializer(request.user.productcart_set.all(), many=True).data)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def manage_cart(request, pk):
    """Метод позволяет авторизованному пользователю управлять корзиной:
    обновлять кол-во определенного товара или удалять позицию из своей корзины"""
    cart_item = request.user.productcart_set.filter(id=pk).first()

    if cart_item is None:
        return Response({"error": "Desired cart item does not exist."}, status=400)

    if request.method == "POST":
        action = request.data.get("action")
        if action != "add" and action != "remove":
            return Response({"error": "Unavailable action"}, status=405)
        cart_item.change_count(action)

    if request.method == "DELETE":
        cart_item.delete()

    return Response(CartStoreSerializer(cart_item, many=False).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_cart(request):
    """Метод позволяет авторизованному пользователю добавлять опредленный товар в корзину"""
    product_id = request.data.get("productId")
    type_ = request.data.get("type")
    size = request.data.get("size")

    # Ищем доустпный товар с переданными параметрами
    product_item = ProductItem.objects.filter(product_id=product_id, type=type_).first()

    # Если такого нет, то возвращаем ошибку
    if product_item is None:
        return Response({"error": "Desired product item does not exist."}, status=400)

    # Если у товара должен быть размер, но не передан, то возвращаем ошибку
    if product_item.product.have_size and size is None:
        return Response({"error": "Product must have the size."}, status=400)

    # Если товар не имеет переданного размера, то возвращаем ошибку
    if not product_item.check_size(size):
        return Response({"error": "Product does not have this size."}, status=400)

    # Проверяет, есть ли у пользователя данный товар в корзине, если есть, то возвращает ошибку
    if product_item.product.have_size and \
            request.user.productcart_set.filter(
                product_item=product_item, size=product_item.sizes.get(size=size)
            ).exists():
        return Response({"error": "Product is already in the cart."}, status=400)

    request.data['user'] = request.user.id
    request.data['product_item'] = product_item.id
    request.data['size'] = product_item.sizes.get(size=size).id if product_item.product.have_size else None

    serializer = ProductCartPureSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            CartStoreSerializer(request.user.productcart_set.get(id=serializer.data.get("id")), many=False).data
        )
    return Response(serializer.errors, status=500)
