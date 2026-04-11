from django.db.models import Avg
from django.db.models.functions import Coalesce
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse

from products.models import Product
from news.models import News
from .forms import ContactForm


def index(request):
    popular_products = (
        Product.objects.annotate(
            avg_rating=Coalesce(Avg('ratings__stars'), 0.0)
        )
        .order_by('-avg_rating', '-id')
    )[:24]

    news = News.objects.filter(
        is_published=True
    ).order_by('-published_at')[:24]

    return render(request, 'index.html', {
        'products': popular_products,
        'news': news,
    })


def about(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            phone_number = form.cleaned_data['phone_number']

            subject = f"Новое сообщение от {name}"
            body = (
                f"Сообщение от: {name} ({email})\n\n"
                f"{message}\n\n"
                f"Телефон: {phone_number}"
            )

            send_mail(
                subject,
                body,
                email,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )

            return redirect(f"{reverse('about')}?sent=1")
    else:
        form = ContactForm()

    return render(request, 'about.html', {
        'form': form,
        'form_sent': request.GET.get('sent') == '1',
    })


def contact_view(request):
    return redirect('about')