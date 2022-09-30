from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from io import BytesIO

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer


# Изменить название на UserInfo
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, null=False, blank=True)
    last_name = models.CharField(max_length=100, null=False, blank=True)
    patronymic = models.CharField(max_length=100, null=False, blank=True, default="")
    balance = models.PositiveSmallIntegerField(default=0)

    class RoleChoice(models.TextChoices):
        administrator = "Administrator"
        moderator = "Moderator"
        employee = "Employee"

    role = models.CharField(max_length=len(RoleChoice.administrator), choices=RoleChoice.choices,
                            default=RoleChoice.employee, null=False, blank=False)

    class Meta:
        verbose_name = "Покупатель"
        verbose_name_plural = "Покупатели"

    def increase_balance(self, delta: int):
        self.balance += delta
        self.save()

    def decrease_balance(self, delta: int):
        if self.balance < delta:
            raise ValidationError("User balance must not be negative")
        self.balance -= delta
        self.save()

    def cart_total_count(self):
        return sum([c.price() * c.count for c in self.user.productcart_set.all()])

    def clear_cart(self):
        return [item.delete() for item in self.user.productcart_set.all()]

    def name(self):
        """
        Join and return stripped customer name
        """
        return " ".join([self.last_name, self.first_name, self.patronymic]).strip()

    def extract_cart(self):
        return [
            {
                "product_id": c.product_id(),
                "name": c.name(),
                "type": c.type(),
                "item_size": c.item_size(),
                "photo": c.photo(),
                "price": c.price(),
                "count": c.count,
                "theme": c.theme(),
            } for c in self.user.productcart_set.all()
        ]


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_list = models.BinaryField(null=False, blank=False)

    class PaymentMethodChoice(models.TextChoices):
        ucoins = "ucoins"
        rubles = "rubles"

    payment_method = models.CharField(max_length=6, choices=PaymentMethodChoice.choices,
                                      default=PaymentMethodChoice.ucoins, null=False, blank=False)

    class OfficeChoice(models.TextChoices):
        mira = "Mira"
        lenina = "Lenina"
        yasnaya = "Yasnaya"

    office = models.CharField(max_length=len(OfficeChoice.yasnaya), choices=OfficeChoice.choices,
                              default=OfficeChoice.lenina, null=False, blank=False)

    class OrderStateChoice(models.TextChoices):
        accepted = "Accepted"
        formed = "Formed"
        completed = "Completed"

    state = models.CharField(max_length=len(OrderStateChoice.completed), choices=OrderStateChoice.choices,
                             default=OrderStateChoice.accepted, null=False, blank=False)

    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_date']

    def products(self):
        return JSONParser().parse(BytesIO(self.product_list))

    def user_name(self):
        return self.user.customer.name()

    def set_state(self, state_=None):
        if state_ is None:
            return
        if state_ not in self.OrderStateChoice.values:
            return
        self.state = state_
        self.save()

    def set_product_list(self, list_):
        self.product_list = JSONRenderer().render(list_)
        self.save()
