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

    # Стоимость товаров
    total_price_without_discount = sum(item.product.price * item.quantity for item in cart_items)
    total_price_with_discount = sum(item.product.get_discounted_price() * item.quantity for item in cart_items)

    # Стоимость доставки
    delivery_method = request.POST.get('delivery_method', 'standard')  # По умолчанию 'standard'
    delivery_cost = 200 if delivery_method == 'standard' else 500  # Стоимость доставки по умолчанию

    # Рассчитываем общую сумму
    total_without_discount = total_price_without_discount + delivery_cost
    total_with_discount = total_price_with_discount + delivery_cost

    # Если это AJAX запрос
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'total_price_without_discount': total_price_without_discount,
            'total_price_with_discount': total_price_with_discount,
            'delivery_cost': delivery_cost,
            'total_without_discount': total_without_discount,
            'total_with_discount': total_with_discount,
        })

    # Если это POST-запрос (отправка формы)
    if request.method == 'POST':
        address = request.POST['address']

        # Создаем заказ без передачи total_price
        order = Order.objects.create(
            user=user,
            address=address,
            delivery_method=delivery_method,
            # total_price не передаем, так как это вычисляемое свойство
        )

        # Переносим товары из корзины в заказ и сохраняем информацию о скидке
        for item in cart_items:
            price_at_purchase = item.product.get_discounted_price()
            discount_applied = item.product.get_discounted_price() < item.product.price
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=price_at_purchase,
                discount_applied=discount_applied,
            )

        # Рассчитываем общую цену для заказа
        order_total_price = order.total_price()  # Используем метод total_price, чтобы получить итоговую сумму
        # Применяем расчет к заказу, если нужно, например, обновить заказ
        order.total_price = order_total_price  # Если вы хотите хранить итоговую сумму
        order.save()

        # Очищаем корзину
        cart_items.delete()

        # Оповещаем пользователя
        return redirect('orders:order_success', order_id=order.id)

    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'total_price_without_discount': total_price_without_discount,
        'total_price_with_discount': total_price_with_discount,
        'delivery_cost': delivery_cost,
        'total_without_discount': total_without_discount,
        'total_with_discount': total_with_discount,
    })



@login_required
def order_success(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})