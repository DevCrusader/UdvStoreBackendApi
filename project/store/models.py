from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db import models
from django.contrib.auth.models import User
from django.db.models import UniqueConstraint, CheckConstraint


# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    price = models.PositiveSmallIntegerField(default=100)
    description = models.TextField(max_length=500, null=False, blank=True)
    have_size = models.BooleanField(default=False, null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False)

    class ThemeChoice(models.TextChoices):
        ussc = 'Ussc'
        udv = 'Udv'

    theme = models.CharField(max_length=len(ThemeChoice.ussc), choices=ThemeChoice.choices,
                             default=ThemeChoice.ussc, null=False, blank=False, db_index=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['created_date']

    def state(self):
        item_list = self.productitem_set.all()
        return all([pi.state == "actual" for pi in item_list]) and bool(item_list)

    def items_list(self):
        return [
            {
                'id': pi.id,
                'type': pi.type,
                'sizes': pi.size_list(),
                'photos': pi.photos()
            } for pi in self.productitem_set.filter(state=ProductItem.StateChoice.actual)
        ]

    def __str__(self):
        return self.name


class Size(models.Model):
    size = models.CharField(max_length=5, null=False, blank=False)

    def __str__(self):
        return f"Size {self.size}"

    class Meta:
        verbose_name = 'Размер'
        verbose_name_plural = 'Размеры'


class ProductItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    type = models.CharField(max_length=100, null=False, blank=False)
    sizes = models.ManyToManyField('Size', blank=True)

    class StateChoice(models.TextChoices):
        actual = "actual"
        hidden = 'hidden'

    state = models.CharField(max_length=len(StateChoice.actual), choices=StateChoice.choices,
                             default=StateChoice.hidden, null=False, blank=False)

    class Meta:
        verbose_name = 'Тип товара'
        verbose_name_plural = 'Типы товаров'
        ordering = ['-product__created_date']
        constraints = [
        ]

    def add_size(self, size):
        if not self.product.have_size:
            raise ValidationError('Product can not be sized')
        if not self.check_size(size):
            raise ValidationError("Product does not have a specified size")
        self.sizes.add(Size.objects.get(size=size))
        self.save()

    def remove_size(self, size):
        if not self.sizes.filter(size=size).exists():
            raise ValidationError('Product does not have a specified size')
        self.sizes.remove(Size.objects.get(size=size))
        self.save()

    def check_size(self, size: str):
        if not self.product.have_size:
            return size is None
        size = Size.objects.get(size=size)
        return size in self.sizes.all()

    def size_list(self):
        if not self.product.have_size:
            return "Product can not be sized"
        sizes_ = self.sizes.all()
        if len(sizes_):
            return [s.size for s in sizes_]
        return "Empty now"

    def set_actual(self):
        if not len(self.productphoto_set.all()):
            raise ValidationError('Product does not have any photos')
        self.state = self.StateChoice.actual
        self.save()

    def set_hidden(self):
        self.state = self.StateChoice.hidden
        self.save()

    def name(self):
        return self.product.name

    def price(self):
        return self.product.price

    def theme(self):
        return self.product.theme

    def photo(self):
        return photo.path() if (photo := self.productphoto_set.first()) else "Some photo path"

    def photos(self):
        return [photo.path() for photo in self.productphoto_set.all()]

    def __str__(self):
        return f"{self.product.name} - {self.type}"


# мб стоит переименовать просто в Photo
class ProductPhoto(models.Model):
    product_item = models.ForeignKey(ProductItem, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to="images/productItemPhotos/")
    main = models.BooleanField(default=False, null=False, blank=False)

    class Meta:
        verbose_name = 'Фото цвета товара'
        verbose_name_plural = 'Фото цветов товаров'
        ordering = ['product_item', '-main']
        constraints = [
            UniqueConstraint(fields=['product_item', ], condition=models.Q(main=True), name='photo_main_constrain')
        ]

    def path(self):
        return "/".join(self.photo.path.split("/")[-2:])

    def __str__(self):
        return f"{self.product_item.product.name} {self.product_item.type} - фото"


# Мб стоит переименовать просто в Cart
class ProductCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_item = models.ForeignKey(ProductItem, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    count = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = 'Позиция в корзине'
        verbose_name_plural = 'Позиции в корзине'

    def name(self):
        return self.product_item.name()

    def type(self):
        return self.product_item.type

    def item_size(self):
        return self.size.size if self.size else None

    def price(self):
        return self.product_item.price()

    def photo(self):
        return self.product_item.photo()

    def product_id(self):
        return self.product_item.product.id

    def theme(self):
        return self.product_item.product.theme

    def change_count(self, action):
        if action == "add":
            if self.count < 10:
                self.count += 1
                return self.save()

        if action == "remove":
            if self.count == 1:
                return self.delete()
            self.count -= 1
            return self.save()
