from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product
from .models import CartItem, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Используем get_or_create для создания или получения элемента корзины
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if created:
        messages.success(request, f"{product.name} добавлен в корзину.")
    else:
        # Увеличиваем количество товара, если он уже есть в корзине
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"Количество товара {product.name} в корзине увеличено.")

    return redirect('orders:cart')  # Перенаправление в корзину или на текущую страницу


@login_required
def decrease_cart(request, product_id):
    cart_item = CartItem.objects.filter(user=request.user, product_id=product_id).first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, f"Количество товара {cart_item.product.name} уменьшено на 1.")
        else:
            cart_item.delete()
            messages.success(request, f"Товар {cart_item.product.name} удалён из корзины.")

    return redirect('orders:cart')


@login_required
def remove_from_cart(request, product_id):
    cart_item = CartItem.objects.filter(user=request.user, product_id=product_id).first()

    if cart_item:
        cart_item.delete()
        messages.success(request, f"Товар {cart_item.product.name} удалён из корзины.")
    else:
        messages.error(request, "Товар не найден в вашей корзине.")

    return redirect('orders:cart')


@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'orders/cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def update_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    action = request.POST.get('action')

    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"Количество товара {cart_item.product.name} увеличено.")
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        messages.success(request, f"Количество товара {cart_item.product.name} уменьшено.")
    elif action == 'remove':
        cart_item.delete()
        messages.success(request, f"Товар {cart_item.product.name} удалён из корзины.")

    return redirect('orders:cart')

from .forms import OrderForm
from django.contrib import messages
from .models import SaleEvent, OrderItem

from django.db import transaction

@login_required
def checkout(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)

    if not cart_items.exists():
        return redirect('products:product_list')  # Корзина пуста

    total_price = sum(item.total_price() for item in cart_items)

    # Устанавливаем стоимость доставки в зависимости от выбора
    delivery_method = request.POST.get('delivery_method', 'standard')  # По умолчанию 'standard'
    if delivery_method == 'express':
        delivery_cost = 500
    else:
        delivery_cost = 200

    # Рассчитываем общую сумму
    total = total_price + delivery_cost
    
    # Используем заголовок для определения, что запрос является AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Отправляем данные обратно на фронтенд в формате JSON
        return JsonResponse({
            'total_price': total_price,
            'delivery_cost': delivery_cost,
            'total': total,
        })

    if request.method == 'POST':
        address = request.POST['address']

        # Создаем заказ
        order = Order.objects.create(
            user=user,
            address=address,
            delivery_method=delivery_method,
            total_price=total,  # Учитываем стоимость товаров и доставку
        )

        # Переносим товары из корзины в заказ
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=item.product.price,
            )

        # Очищаем корзину
        cart_items.delete()

        # Оповещаем пользователя
        return redirect('orders:order_success', order_id=order.id)

    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'delivery_cost': delivery_cost,
        'total': total,  # Общая сумма с учетом доставки
    })


@login_required
def order_success(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})