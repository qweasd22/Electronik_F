from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product
from .forms import OrderForm
from .models import CartItem, Order, OrderItem, SaleEvent


def _redirect_back(request, fallback="orders:cart"):
    return redirect(request.META.get("HTTP_REFERER") or fallback)


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, f'Товар "{product.name}" отсутствует на складе.')
        return _redirect_back(request)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={"quantity": 1},
    )

    if created:
        messages.success(request, f'"{product.name}" добавлен в корзину.')
        return _redirect_back(request)

    if cart_item.quantity >= product.stock:
        messages.warning(
            request,
            f'Нельзя добавить больше {product.stock} шт. товара "{product.name}".'
        )
        return _redirect_back(request)

    cart_item.quantity += 1
    cart_item.save(update_fields=["quantity"])
    messages.success(request, f'Количество товара "{product.name}" в корзине увеличено.')
    return _redirect_back(request)


@login_required
def decrease_cart(request, product_id):
    cart_item = CartItem.objects.filter(user=request.user, product_id=product_id).first()

    if not cart_item:
        messages.error(request, "Товар не найден в корзине.")
        return redirect("orders:cart")

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save(update_fields=["quantity"])
        messages.success(request, f'Количество товара "{cart_item.product.name}" уменьшено на 1.')
    else:
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'Товар "{product_name}" удалён из корзины.')

    return redirect("orders:cart")


@login_required
def remove_from_cart(request, product_id):
    cart_item = CartItem.objects.filter(user=request.user, product_id=product_id).first()

    if cart_item:
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'Товар "{product_name}" удалён из корзины.')
    else:
        messages.error(request, "Товар не найден в вашей корзине.")

    return redirect("orders:cart")


@login_required
def cart_view(request):
    cart_items = CartItem.objects.select_related("product").filter(user=request.user)

    cart_has_errors = False
    total = Decimal("0.00")
    total_units = 0

    for item in cart_items:
        item.available_stock = item.product.stock
        item.is_over_limit = item.quantity > item.product.stock
        item.is_out_of_stock = item.product.stock <= 0

        if item.is_over_limit or item.is_out_of_stock:
            cart_has_errors = True

        total += item.total_price
        total_units += item.quantity

    return render(
        request,
        "orders/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
            "total_units": total_units,
            "cart_has_errors": cart_has_errors,
        },
    )


@login_required
def update_cart(request, cart_item_id):
    cart_item = get_object_or_404(
        CartItem.objects.select_related("product"),
        id=cart_item_id,
        user=request.user,
    )
    action = request.POST.get("action")
    product = cart_item.product

    if action == "increase":
        if product.stock <= 0:
            messages.error(request, f'Товар "{product.name}" отсутствует на складе.')
        elif cart_item.quantity >= product.stock:
            messages.warning(
                request,
                f'Нельзя добавить больше {product.stock} шт. товара "{product.name}".'
            )
        else:
            cart_item.quantity += 1
            cart_item.save(update_fields=["quantity"])
            messages.success(request, f'Количество товара "{product.name}" увеличено.')

    elif action == "decrease":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save(update_fields=["quantity"])
            messages.success(request, f'Количество товара "{product.name}" уменьшено.')
        else:
            cart_item.delete()
            messages.success(request, f'Товар "{product.name}" удалён из корзины.')

    elif action == "remove":
        cart_item.delete()
        messages.success(request, f'Товар "{product.name}" удалён из корзины.')

    else:
        messages.error(request, "Некорректное действие.")

    return redirect("orders:cart")


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("courier", "user").prefetch_related("items__product", "status_history"),
        id=order_id,
        user=request.user,
    )
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
@transaction.atomic
def checkout(request):
    user = request.user
    cart_items = CartItem.objects.select_related("product").filter(user=user)

    if not cart_items.exists():
        messages.warning(request, "Корзина пуста.")
        return redirect("products:product_list")

    total_price_without_discount = Decimal("0.00")
    total_price_with_discount = Decimal("0.00")

    for item in cart_items:
        total_price_without_discount += item.product.price * item.quantity
        total_price_with_discount += item.product.get_discounted_price() * item.quantity

    delivery_method = request.POST.get("delivery_method", "standard")
    delivery_cost = Order.DELIVERY_COST.get(delivery_method, Decimal("200.00"))

    total_without_discount = total_price_without_discount + delivery_cost
    total_with_discount = total_price_with_discount + delivery_cost

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "delivery_cost": str(delivery_cost),
            "total_without_discount": str(total_without_discount),
            "total_with_discount": str(total_with_discount),
        })

    if request.method == "POST":
        form = OrderForm(request.POST, user=user)

        if not form.is_valid():
            return render(request, "orders/checkout.html", {
                "form": form,
                "cart_items": cart_items,
                "delivery_method": delivery_method,
                "delivery_cost": delivery_cost,
                "total_without_discount": total_without_discount,
                "total_with_discount": total_with_discount,
            })

        locked_products = {}
        for item in cart_items:
            locked_product = Product.objects.select_for_update().get(id=item.product_id)
            locked_products[item.product_id] = locked_product

            if locked_product.stock <= 0:
                messages.error(request, f'Товар "{locked_product.name}" закончился.')
                return redirect("orders:cart")

            if item.quantity > locked_product.stock:
                messages.error(
                    request,
                    f'Для товара "{locked_product.name}" доступно только {locked_product.stock} шт.'
                )
                return redirect("orders:cart")

        order = form.save(commit=False)
        order.user = user

        if not order.recipient_name:
            full_name = f"{user.first_name} {user.last_name}".strip()
            order.recipient_name = full_name or user.username

        if not order.phone_number and getattr(user, "phone_number", None):
            order.phone_number = user.phone_number

        order.save()

        for item in cart_items:
            product = locked_products[item.product_id]
            price_at_purchase = product.get_discounted_price()
            discount_applied = price_at_purchase < product.price

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price_at_purchase=price_at_purchase,
                discount_applied=discount_applied,
            )

            product.stock -= item.quantity
            product.save(update_fields=["stock"])

            SaleEvent.objects.create(
                user=user,
                action="purchase",
                order=order,
                product=product,
                quantity=item.quantity,
                total_price=price_at_purchase * item.quantity,
            )

        cart_items.delete()

        messages.success(request, "Заказ успешно оформлен.")
        return redirect("orders:order_success", order_id=order.id)

    form = OrderForm(user=user)

    return render(request, "orders/checkout.html", {
        "form": form,
        "cart_items": cart_items,
        "delivery_method": delivery_method,
        "delivery_cost": delivery_cost,
        "total_without_discount": total_without_discount,
        "total_with_discount": total_with_discount,
    })


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/order_success.html", {"order": order})