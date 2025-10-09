from django.db import models
from accounts.models import CustomUser
from products.models import Product
from django.utils import timezone

class CartItem(models.Model):
    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("Количество", default=1)

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Корзина"

    def total_price(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.user.username})"

class Order(models.Model):
    DELIVERY_CHOICES = [
        ('standard', 'Обычная доставка'),
        ('express', 'Экспресс доставка'),
    ]

    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Дата создания", default=timezone.now)
    address = models.TextField("Адрес доставки")
    delivery_method = models.CharField("Способ доставки", max_length=50, choices=DELIVERY_CHOICES)
    is_paid = models.BooleanField("Оплачен", default=False)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def __str__(self):
        return f"Заказ {self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name="Заказ", related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("Количество", default=1)

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

    def total_price(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
