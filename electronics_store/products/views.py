from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Review, Rating, Category, Brand
from .forms import ProductFilterForm, ReviewForm, RatingForm
from django.contrib.auth.decorators import login_required
from orders.models import CartItem
from django.db.models import Q
def product_list(request):
    # Используем форму для фильтрации
    form = ProductFilterForm(request.GET or None)
    products = Product.objects.all()

    if form.is_valid():
        category = form.cleaned_data.get('category')
        brand = form.cleaned_data.get('brand')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        search = form.cleaned_data.get('search')

        # Фильтрация по ForeignKey корректно
        if category:
            products = products.filter(category__id=category.id)
        if brand:
            products = products.filter(brand__id=brand.id)
        if min_price is not None:
            products = products.filter(price__gte=min_price)
        if max_price is not None:
            products = products.filter(price__lte=max_price)
        if search:
            products = products.filter(name__icontains=search)

    # Корзина пользователя
    cart_items = {}
    if request.user.is_authenticated:
        user_cart = CartItem.objects.filter(user=request.user)
        cart_items = {item.product.id: item.quantity for item in user_cart}

    # Передаём категории и бренды для фильтров
    categories = Category.objects.all()
    brands = Brand.objects.all()

    context = {
        'products': products,
        'form': form,
        'cart_items': cart_items,
        'categories': categories,
        'brands': brands,
        'selected_category': form.cleaned_data.get('category') if form.is_valid() else None,
        'selected_brand': form.cleaned_data.get('brand') if form.is_valid() else None,
        'selected_min_price': form.cleaned_data.get('min_price') if form.is_valid() else '',
        'selected_max_price': form.cleaned_data.get('max_price') if form.is_valid() else '',
        'selected_search': form.cleaned_data.get('search') if form.is_valid() else '',
    }

    return render(request, 'products/product_list.html', context)


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    reviews = product.reviews.filter(is_approved=True)
    average_rating = product.average_rating()

    ratings_for_product = Rating.objects.filter(product=product)

    # Проверка количества товара в корзине
    quantity_in_cart = 0
    if request.user.is_authenticated:
        cart_item = CartItem.objects.filter(user=request.user, product=product).first()
        if cart_item:
            quantity_in_cart = cart_item.quantity

    if request.method == 'POST' and request.user.is_authenticated:
        review_form = ReviewForm(request.POST)
        rating_form = RatingForm(request.POST)

        if review_form.is_valid() and rating_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()

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
        'ratings_for_product': ratings_for_product,
        'review_form': review_form,
        'rating_form': rating_form,
        'quantity_in_cart': quantity_in_cart
    })