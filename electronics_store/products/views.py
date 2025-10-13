from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Review, Rating
from .forms import ProductFilterForm, ReviewForm, RatingForm
from django.contrib.auth.decorators import login_required

from django.shortcuts import render
from .models import Product, Category, Brand
from orders.models import CartItem

def product_list(request):
    # Получаем данные из GET-запроса
    category_filter = request.GET.get('category')
    brand_filter = request.GET.get('brand')
    min_price_filter = request.GET.get('min_price')
    max_price_filter = request.GET.get('max_price')
    search_filter = request.GET.get('search')

    # Начальный запрос для всех товаров
    products = Product.objects.all()

    # Фильтрация по категории
    if category_filter:
        products = products.filter(category__id=category_filter)

    # Фильтрация по бренду
    if brand_filter:
        products = products.filter(brand__id=brand_filter)

    # Фильтрация по минимальной цене
    if min_price_filter:
        try:
            products = products.filter(price__gte=float(min_price_filter))
        except ValueError:
            pass  # Если не удалось преобразовать в число, не применяем фильтр

    # Фильтрация по максимальной цене
    if max_price_filter:
        try:
            products = products.filter(price__lte=float(max_price_filter))
        except ValueError:
            pass  # Если не удалось преобразовать в число, не применяем фильтр

    # Фильтрация по названию товара
    if search_filter and search_filter != 'None':
        products = products.filter(name__icontains=search_filter)

    # Получаем список категорий и брендов для фильтрации в форме
    categories = Category.objects.all()
    brands = Brand.objects.all()

    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'brands': brands,
        'selected_category': category_filter,
        'selected_brand': brand_filter,
        'selected_min_price': min_price_filter,
        'selected_max_price': max_price_filter,
        'selected_search': search_filter,
    })



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