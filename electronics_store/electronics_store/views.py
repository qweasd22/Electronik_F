from django.db.models import Avg
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.core.paginator import Paginator
from products.models import Product
from news.models import News

def index(request):
    popular_products_qs = (
        Product.objects.annotate(
            avg_rating=Coalesce(Avg('ratings__stars'), 0.0)
        )
        .order_by('-avg_rating', '-id')
    )

    news_qs = News.objects.filter(
        is_published=True
    ).order_by('-published_at')

    products_paginator = Paginator(popular_products_qs, 4)
    news_paginator = Paginator(news_qs, 3)

    products_page_obj = products_paginator.get_page(request.GET.get('products_page', 1))
    news_page_obj = news_paginator.get_page(request.GET.get('news_page', 1))

    return render(request, 'index.html', {
        'products_page_obj': products_page_obj,
        'news_page_obj': news_page_obj,
    })
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
from .forms import ContactForm
from django.http import HttpResponseRedirect

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Получаем данные из формы
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            phone_number = form.cleaned_data['phone_number']

            # Отправляем уведомление на email администратора
            subject = f"Новое сообщение от {name}"
            body = f"Сообщение от: {name} ({email})\n\n{message},\n\nТелефон: {phone_number}"
            send_mail(
                subject,
                body,
                email,  # email отправителя
                [settings.ADMIN_EMAIL],  # email администратора из настроек
                fail_silently=False,
            )

            
            messages.success(request, "Ваше сообщение отправлено. Мы свяжемся с вами в ближайшее время.")

            # Перенаправляем на ту же страницу, чтобы избежать повторной отправки формы при обновлении
            return HttpResponseRedirect(request.path_info)
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


def about(request):
    return render(request, 'about.html')    