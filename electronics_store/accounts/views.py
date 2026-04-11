from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from orders.models import Order


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            if CustomUser.objects.filter(username=username).exists():
                form.add_error('username', 'Это имя пользователя уже занято. Пожалуйста, выберите другое.')
                return render(request, 'accounts/signup.html', {'form': form})
            elif CustomUser.objects.filter(email=email).exists():
                form.add_error('email', 'Этот email уже занят. Пожалуйста, выберите другой.')
                return render(request, 'accounts/signup.html', {'form': form})

            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('accounts:profile')
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/signup.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')

            messages.error(request, "Неверный логин или пароль.")
        else:
            messages.error(request, "Неверный логин или пароль.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные успешно обновлены.')
            return redirect('accounts:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)

    current_orders = (
        Order.objects
        .filter(user=request.user, status__in=['processing', 'paid', 'shipped'])
        .prefetch_related('items__product')
        .order_by('-created_at')
    )

    order_history = (
        Order.objects
        .filter(user=request.user, status__in=['delivered', 'cancelled'])
        .prefetch_related('items__product')
        .order_by('-created_at')
    )

    all_orders = Order.objects.filter(user=request.user)

    context = {
        'form': form,
        'current_orders': current_orders,
        'order_history': order_history,
        'stats': {
            'total': all_orders.count(),
            'current': current_orders.count(),
            'delivered': all_orders.filter(status='delivered').count(),
            'cancelled': all_orders.filter(status='cancelled').count(),
        }
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        id=order_id,
        user=request.user
    )
    return render(request, 'accounts/order_detail.html', {'order': order})


from django.db import transaction

@transaction.atomic
def cancel_order(self):
    if self.status == "delivered":
        raise ValueError("Заказ уже доставлен и не может быть отменен.")
    if self.status == "cancelled":
        raise ValueError("Заказ уже отменен.")

    for item in self.items.select_related("product"):
        item.product.stock += item.quantity
        item.product.save(update_fields=["stock"])

    self.status = "cancelled"
    self.save(update_fields=["status"])