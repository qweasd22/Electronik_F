from decimal import Decimal
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
        # Используем метод .price продукта для расчета цены
        try:
            if self.product is None or self.quantity is None:
                raise ValueError("Product or quantity is None")
            return self.quantity * self.product.price
        except AttributeError:
            raise ValueError("Product or quantity does not have required attribute")

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.user.username})"


class Order(models.Model):
    DELIVERY_CHOICES = [
        ('standard', 'Обычная доставка'),
        ('express', 'Экспресс доставка'),
    ]

    STATUS_CHOICES = [
        ('processing', 'В обработке'),
        ('paid', 'Оплачен'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
    ]

    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Дата создания", default=timezone.now)
    address = models.TextField("Адрес доставки")
    delivery_method = models.CharField("Способ доставки", max_length=50, choices=DELIVERY_CHOICES)
    is_paid = models.BooleanField("Оплачен", default=False)
    status = models.CharField("Статус заказа", max_length=20, choices=STATUS_CHOICES, default='processing')

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def total_price(self):
        total = Decimal(0)
        for item in self.items.all():
            total += item.total_price  # Используем свойство total_price
        return total

    def __str__(self):
        return f"Заказ {self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name="Заказ", related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("Количество", default=1)
    price_at_purchase = models.DecimalField("Цена на момент покупки", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

    @property
    def total_price(self):
        if self.price_at_purchase is None or self.quantity is None:
            return Decimal(0)  # Верните 0, если одно из полей None
        return self.quantity * self.price_at_purchase

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"


class SaleEvent(models.Model):
    ACTION_CHOICES = [
        ('purchase', 'Purchase'),  # Оформление заказа
        ('refund', 'Refund'),  # Возврат товара
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="Тип события")  # Тип события (покупка или возврат)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Заказ")  # Заказ, связанный с событием
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт")  # Продукт, связанный с событием
    quantity = models.PositiveIntegerField(verbose_name="Количество")  # Количество проданных товаров
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")  # Сумма для этого события
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время события")  # Время события

    def __str__(self):
        return f"SaleEvent {self.id} for order {self.order.id} by {self.user.username} on {self.timestamp}"
