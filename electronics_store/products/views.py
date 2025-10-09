# products/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Review, Rating
from .forms import ProductFilterForm, ReviewForm, RatingForm
from django.contrib.auth.decorators import login_required

def product_list(request):
    form = ProductFilterForm(request.GET)
    products = Product.objects.all()

    if form.is_valid():
        category = form.cleaned_data.get('category')
        brand = form.cleaned_data.get('brand')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        search = form.cleaned_data.get('search')

        if category:
            products = products.filter(category=category)
        if brand:
            products = products.filter(brand=brand)
        if min_price is not None:
            products = products.filter(price__gte=min_price)
        if max_price is not None:
            products = products.filter(price__lte=max_price)
        if search:
            products = products.filter(name__icontains=search)

    return render(request, 'products/product_list.html', {'products': products, 'form': form})


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    reviews = product.reviews.filter(is_approved=True)  # Показываем только одобренные отзывы
    average_rating = product.average_rating()  # Средний рейтинг продукта

    # Получаем все рейтинги для продукта (для использования в шаблоне)
    ratings_for_product = Rating.objects.filter(product=product)

    # Обработка формы отзыва
    if request.method == 'POST' and request.user.is_authenticated:
        review_form = ReviewForm(request.POST)
        rating_form = RatingForm(request.POST)

        if review_form.is_valid() and rating_form.is_valid():
            # Сохраняем отзыв
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()

            # Сохраняем рейтинг
            rating = rating_form.save(commit=False)
            rating.product = product
            rating.user = request.user
            rating.save()

            return redirect('products:product_detail', id=product.id)
    else:
        review_form = ReviewForm()
        rating_form = RatingForm()

    return render(request, 'products/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'average_rating': average_rating,
        'ratings_for_product': ratings_for_product,  # Передаем все рейтинги для продукта
        'review_form': review_form,
        'rating_form': rating_form,
    })