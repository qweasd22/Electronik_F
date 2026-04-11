from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from accounts.models import CustomUser
from products.models import Product


class CartItem(models.Model):
    user = models.ForeignKey(
        CustomUser,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    product = models.ForeignKey(
        Product,
        verbose_name="Товар",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField("Количество", default=1)

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Корзина"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_cart_item",
            )
        ]

    def clean(self):
        if self.quantity < 1:
            raise ValidationError({"quantity": "Количество должно быть не меньше 1."})

        if self.product_id and self.quantity > self.product.stock:
            raise ValidationError({
                "quantity": f"Нельзя добавить больше {self.product.stock} шт. товара."
            })

    @property
    def total_price(self):
        if not self.product or self.quantity is None:
            return Decimal("0.00")
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.user.username})"


class Order(models.Model):
    DELIVERY_CHOICES = [
        ("standard", "Обычная доставка"),
        ("express", "Экспресс доставка"),
    ]

    PAYMENT_CHOICES = [
        ("card", "Картой"),
        ("cash", "Наличными"),
    ]

    STATUS_CHOICES = [
        ("processing", "В обработке"),
        ("paid", "Оплачен"),
        ("shipped", "Отправлен"),
        ("delivered", "Доставлен"),
        ("cancelled", "Отменен"),
    ]

    DELIVERY_COST = {
        "standard": Decimal("200.00"),
        "express": Decimal("500.00"),
    }

    user = models.ForeignKey(
        CustomUser,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    courier = models.ForeignKey(
        CustomUser,
        verbose_name="Курьер",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courier_orders",
    )

    created_at = models.DateTimeField("Дата создания", default=timezone.now)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    recipient_name = models.CharField(
        "Имя получателя",
        max_length=255,
        blank=True,
        default="",
    )
    phone_number = models.CharField(
        "Телефон получателя",
        max_length=11,
        blank=True,
        default="",
    )
    address = models.TextField("Адрес доставки")

    delivery_method = models.CharField(
        "Способ доставки",
        max_length=50,
        choices=DELIVERY_CHOICES,
        default="standard",
    )
    payment_method = models.CharField(
        "Способ оплаты",
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="card",
    )

    comment = models.TextField("Комментарий к заказу", blank=True)
    tracking_note = models.CharField(
        "Комментарий по статусу",
        max_length=255,
        blank=True,
        default="",
    )

    is_paid = models.BooleanField("Оплачен", default=False)
    status = models.CharField(
        "Статус заказа",
        max_length=20,
        choices=STATUS_CHOICES,
        default="processing",
    )

    paid_at = models.DateTimeField("Дата оплаты", null=True, blank=True)
    shipped_at = models.DateTimeField("Дата отправки", null=True, blank=True)
    delivered_at = models.DateTimeField("Дата доставки", null=True, blank=True)
    cancelled_at = models.DateTimeField("Дата отмены", null=True, blank=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def clean(self):
        if self.phone_number:
            if not self.phone_number.isdigit():
                raise ValidationError({"phone_number": "Телефон должен содержать только цифры."})
            if len(self.phone_number) != 11:
                raise ValidationError({"phone_number": "Телефон должен содержать ровно 11 цифр."})

    def save(self, *args, **kwargs):
        is_created = self._state.adding
        super().save(*args, **kwargs)

        if is_created:
            OrderStatusHistory.objects.create(
                order=self,
                status=self.status,
                note="Заказ создан",
            )

    @property
    def delivery_cost(self):
        return self.DELIVERY_COST.get(self.delivery_method, Decimal("0.00"))

    @property
    def items_total(self):
        return sum(
            (item.total_price for item in self.items.all()),
            Decimal("0.00"),
        )

    @property
    def total_price(self):
        return self.items_total + self.delivery_cost

    @property
    def can_be_cancelled(self):
        return self.status not in {"delivered", "cancelled"}

    def set_status(self, new_status, note="", changed_by=None):
        valid_statuses = {choice[0] for choice in self.STATUS_CHOICES}
        if new_status not in valid_statuses:
            raise ValueError("Некорректный статус заказа.")

        now = timezone.now()
        update_fields = ["status", "updated_at"]

        self.status = new_status

        if note:
            self.tracking_note = note
            update_fields.append("tracking_note")

        if new_status == "paid":
            self.is_paid = True
            self.paid_at = now
            update_fields.extend(["is_paid", "paid_at"])

        elif new_status == "shipped":
            self.shipped_at = now
            update_fields.append("shipped_at")

        elif new_status == "delivered":
            self.delivered_at = now
            update_fields.append("delivered_at")

        elif new_status == "cancelled":
            self.cancelled_at = now
            update_fields.append("cancelled_at")

        self.save(update_fields=list(set(update_fields)))

        OrderStatusHistory.objects.create(
            order=self,
            status=new_status,
            note=note,
            changed_by=changed_by,
        )

    @transaction.atomic
    def cancel(self, note="Заказ отменен пользователем", changed_by=None):
        if self.status == "delivered":
            raise ValueError("Заказ уже доставлен и не может быть отменен.")

        if self.status == "cancelled":
            raise ValueError("Заказ уже отменен.")

        for item in self.items.select_related("product"):
            item.product.stock += item.quantity
            item.product.save(update_fields=["stock"])

            SaleEvent.objects.create(
                user=self.user,
                action="refund",
                order=self,
                product=item.product,
                quantity=item.quantity,
                total_price=item.total_price,
            )

        self.set_status("cancelled", note=note, changed_by=changed_by)

    def __str__(self):
        return f"Заказ #{self.id} — {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        verbose_name="Товар",
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    product_name = models.CharField(
        "Название товара на момент покупки",
        max_length=255,
        blank=True,
        default="",
    )
    quantity = models.PositiveIntegerField("Количество", default=1)
    price_at_purchase = models.DecimalField(
        "Цена на момент покупки",
        max_digits=10,
        decimal_places=2,
    )
    discount_applied = models.BooleanField("Скидка применена", default=False)

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

    def clean(self):
        if self.quantity < 1:
            raise ValidationError({"quantity": "Количество должно быть не меньше 1."})

    def save(self, *args, **kwargs):
        if self.product and not self.product_name:
            self.product_name = self.product.name
        super().save(*args, **kwargs)

    @property
    def total_price(self):
        if self.price_at_purchase is None or self.quantity is None:
            return Decimal("0.00")
        return self.quantity * self.price_at_purchase

    def __str__(self):
        return f"{self.product_name or self.product.name} ({self.quantity})"


class SaleEvent(models.Model):
    ACTION_CHOICES = [
        ("purchase", "Покупка"),
        ("refund", "Возврат"),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="sale_events",
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name="Тип события",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        verbose_name="Заказ",
        related_name="sale_events",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Продукт",
        related_name="sale_events",
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время события",
    )

    class Meta:
        verbose_name = "Событие продажи"
        verbose_name_plural = "События продаж"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.get_action_display()} #{self.id} по заказу #{self.order.id}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Order.STATUS_CHOICES,
    )
    note = models.CharField(
        "Комментарий",
        max_length=255,
        blank=True,
        default="",
    )
    changed_by = models.ForeignKey(
        CustomUser,
        verbose_name="Кем изменено",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="changed_order_statuses",
    )
    created_at = models.DateTimeField("Дата изменения", auto_now_add=True)

    class Meta:
        verbose_name = "История статуса заказа"
        verbose_name_plural = "История статусов заказов"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ #{self.order.id} — {self.get_status_display()}"