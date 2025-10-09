# products/views.py
from django.shortcuts import render, get_object_or_404
from .models import Product
from .forms import ProductFilterForm

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'products/product_detail.html', {'product': product})
# Список продуктов с фильтрацией
def product_list(request):
    form = ProductFilterForm(request.GET)
    products = Product.objects.all()

    # Применяем фильтрацию по данным формы
    if form.is_valid():
        category = form.cleaned_data.get('category')
        if category:
            products = products.filter(category=category)

        brand = form.cleaned_data.get('brand')
        if brand:
            products = products.filter(brand=brand)

        min_price = form.cleaned_data.get('min_price')
        if min_price is not None:
            products = products.filter(price__gte=min_price)

        max_price = form.cleaned_data.get('max_price')
        if max_price is not None:
            products = products.filter(price__lte=max_price)

        search = form.cleaned_data.get('search')
        if search:
            products = products.filter(name__icontains=search)

    return render(request, 'products/product_list.html', {'products': products, 'form': form})

# Подробности о продукте

