from django.db.models import Avg
from products.models import Product
from django.shortcuts import render

def index(request):
    # Используем аннотирование для вычисления среднего рейтинга
    popular_products = Product.objects.annotate(
        avg_rating=Avg('ratings__stars')
    ).filter(avg_rating__gt=4).order_by('-avg_rating')

    return render(request, 'index.html', {
        'products': popular_products,
    })
