from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.core.paginator import Paginator

from .models import Product, Review, Rating, Category, Brand
from .forms import ProductFilterForm, ReviewForm, RatingForm
from orders.models import CartItem


def product_list(request):
    form = ProductFilterForm(request.GET or None)

    products = Product.objects.select_related("category", "brand").prefetch_related("images")

    if form.is_valid():
        category = form.cleaned_data.get("category")
        brand = form.cleaned_data.get("brand")
        min_price = form.cleaned_data.get("min_price")
        max_price = form.cleaned_data.get("max_price")
        search = form.cleaned_data.get("search")

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

    cart_items = {}
    if request.user.is_authenticated:
        user_cart = CartItem.objects.filter(user=request.user).select_related("product")
        cart_items = {item.product_id: item.quantity for item in user_cart}

    paginator = Paginator(products, 4)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    products = list(page_obj.object_list)
    for product in products:
        product.quantity_in_cart = cart_items.get(product.id, 0)

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")
    pagination_query = query_params.urlencode()

    context = {
        "products": products,
        "page_obj": page_obj,
        "form": form,
        "categories": Category.objects.all(),
        "brands": Brand.objects.all(),
        "pagination_query": pagination_query,
        "selected_category_id": form.cleaned_data["category"].id if form.is_valid() and form.cleaned_data.get("category") else "",
        "selected_brand_id": form.cleaned_data["brand"].id if form.is_valid() and form.cleaned_data.get("brand") else "",
        "selected_min_price": form.cleaned_data.get("min_price") if form.is_valid() else "",
        "selected_max_price": form.cleaned_data.get("max_price") if form.is_valid() else "",
        "selected_search": form.cleaned_data.get("search") if form.is_valid() else "",
    }

    return render(request, "products/product_list.html", context)


def product_detail(request, id):
    product = get_object_or_404(
        Product.objects.select_related("category", "brand").prefetch_related(
            "images",
            Prefetch(
                "reviews",
                queryset=Review.objects.filter(is_approved=True).select_related("user")
            ),
            Prefetch(
                "ratings",
                queryset=Rating.objects.select_related("user")
            ),
        ),
        id=id
    )

    reviews = product.reviews.all()
    average_rating = product.average_rating()
    ratings_map = {rating.user_id: rating for rating in product.ratings.all()}

    quantity_in_cart = 0
    user_rating = None

    if request.user.is_authenticated:
        cart_item = CartItem.objects.filter(user=request.user, product=product).first()
        if cart_item:
            quantity_in_cart = cart_item.quantity
        user_rating = ratings_map.get(request.user.id)

    if request.method == "POST" and request.user.is_authenticated:
        review_form = ReviewForm(request.POST)
        rating_form = RatingForm(request.POST)

        if review_form.is_valid() and rating_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()

            Rating.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={"stars": rating_form.cleaned_data["stars"]},
            )

            return redirect("products:product_detail", id=product.id)
    else:
        review_form = ReviewForm()
        rating_form = RatingForm(initial={"stars": user_rating.stars if user_rating else None})

    return render(request, "products/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "average_rating": average_rating,
        "review_form": review_form,
        "rating_form": rating_form,
        "quantity_in_cart": quantity_in_cart,
        "ratings_map": ratings_map,
    })
