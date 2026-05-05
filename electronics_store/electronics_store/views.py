import re

from django.db.models import Avg, Count, Q
from django.db.models.functions import Coalesce
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from orders.models import CartItem, Order
from products.models import Brand, Category, Product, Review, Sale
from news.models import News
from .forms import ContactForm


def _normalize_question(question):
    return " ".join(question.lower().strip().split())


def _format_money(value):
    return f"{value} ₽"


def _find_products(question):
    tokens = [
        token for token in re.findall(r"[a-zа-яё0-9]+", question.lower())
        if len(token) >= 3
    ][:6]

    queryset = Product.objects.select_related("category", "brand").prefetch_related("sales")
    if not tokens:
        return queryset.none()

    condition = Q()
    for token in tokens:
        condition |= (
            Q(name__icontains=token)
            | Q(description__icontains=token)
            | Q(additional_info__icontains=token)
            | Q(category__name__icontains=token)
            | Q(brand__name__icontains=token)
        )

    return queryset.filter(condition).distinct()


def _product_line(product):
    stock_text = f"в наличии {product.stock} шт." if product.stock > 0 else "нет в наличии"
    discounted_price = product.get_discounted_price()
    price_text = _format_money(product.price)

    if discounted_price < product.price:
        price_text = f"{_format_money(discounted_price)} со скидкой, обычная цена {_format_money(product.price)}"

    return (
        f"{product.name}: {price_text}, {stock_text}, "
        f"рейтинг {product.average_rating()}."
    )


def _answer_products(question):
    products = _find_products(question)[:5]
    if not products:
        return None

    lines = [_product_line(product) for product in products]
    return "Нашёл подходящие товары:\n" + "\n".join(f"• {line}" for line in lines)


def _answer_orders(request, question):
    if not any(word in question for word in ["заказ", "статус"]):
        return None

    if not request.user.is_authenticated:
        return "По заказам могу ответить после входа в аккаунт."

    order_id_match = re.search(r"\b\d+\b", question)
    orders = Order.objects.filter(user=request.user).prefetch_related("items__product")

    if order_id_match:
        order = orders.filter(id=int(order_id_match.group())).first()
        if not order:
            return "У вас не найден заказ с таким номером."

        paid_text = "оплачен" if order.is_paid else "не оплачен"
        return (
            f"Заказ #{order.id}: {order.get_status_display()}, {paid_text}. "
            f"Доставка: {order.get_delivery_method_display()}, адрес: {order.address}. "
            f"Сумма: {_format_money(order.total_price)}."
        )

    recent_orders = list(orders.order_by("-created_at")[:3])
    if not recent_orders:
        return "У вас пока нет заказов."

    lines = [
        f"#{order.id}: {order.get_status_display()}, сумма {_format_money(order.total_price)}, "
        f"создан {order.created_at:%d.%m.%Y}"
        for order in recent_orders
    ]
    return "Ваши последние заказы:\n" + "\n".join(f"• {line}" for line in lines)


def _answer_cart(request, question):
    if not any(word in question for word in ["корзин", "cart"]):
        return None

    if not request.user.is_authenticated:
        return "Корзина доступна после входа в аккаунт."

    cart_items = (
        CartItem.objects
        .filter(user=request.user)
        .select_related("product")
        .order_by("product__name")
    )

    if not cart_items:
        return "Ваша корзина сейчас пуста."

    total_quantity = sum(item.quantity for item in cart_items)
    total_price = sum((item.total_price for item in cart_items), start=0)
    lines = [
        f"{item.product.name} — {item.quantity} шт., {_format_money(item.total_price)}"
        for item in cart_items[:5]
    ]

    return (
        f"В корзине {total_quantity} шт. товаров на сумму {_format_money(total_price)}:\n"
        + "\n".join(f"• {line}" for line in lines)
    )


def _answer_catalog(question):
    if "категор" in question:
        categories = Category.objects.annotate(product_count=Count("products")).order_by("name")[:8]
        if categories:
            lines = [f"{category.name} ({category.product_count})" for category in categories]
            return "Категории товаров:\n" + "\n".join(f"• {line}" for line in lines)

    if "бренд" in question or "brand" in question:
        brands = Brand.objects.annotate(product_count=Count("products")).order_by("name")[:8]
        if brands:
            lines = [f"{brand.name} ({brand.product_count})" for brand in brands]
            return "Бренды в каталоге:\n" + "\n".join(f"• {line}" for line in lines)

    return None


def _answer_sales(question):
    if not any(word in question for word in ["скид", "акци", "распрод"]):
        return None

    active_sales = [sale for sale in Sale.objects.prefetch_related("products").order_by("-start_date") if sale.is_current()]
    if not active_sales:
        discounted_products = [
            product for product in Product.objects.prefetch_related("sales").all()[:30]
            if product.get_discounted_price() < product.price
        ][:5]

        if not discounted_products:
            return "Сейчас активных скидок не найдено."

        lines = [
            f"{product.name}: {_format_money(product.get_discounted_price())} вместо {_format_money(product.price)}"
            for product in discounted_products
        ]
        return "Товары со скидкой:\n" + "\n".join(f"• {line}" for line in lines)

    lines = [
        f"{sale.name}: скидка {sale.discount_percentage}%, товаров: {sale.products.count()}"
        for sale in active_sales[:5]
    ]
    return "Активные акции:\n" + "\n".join(f"• {line}" for line in lines)


def _answer_reviews(question):
    if not any(word in question for word in ["рейтинг", "оцен", "отзыв"]):
        return None

    products = _find_products(question)[:3]
    if products:
        lines = []
        for product in products:
            approved_reviews = Review.objects.filter(product=product, is_approved=True).count()
            lines.append(
                f"{product.name}: рейтинг {product.average_rating()}, "
                f"одобренных отзывов {approved_reviews}."
            )
        return "Информация по отзывам:\n" + "\n".join(f"• {line}" for line in lines)

    reviewed_products = (
        Product.objects
        .annotate(avg_rating=Coalesce(Avg("ratings__stars"), 0.0))
        .order_by("-avg_rating", "-id")[:5]
    )
    lines = [f"{product.name}: рейтинг {product.avg_rating:.1f}" for product in reviewed_products]
    return "Самые рейтинговые товары:\n" + "\n".join(f"• {line}" for line in lines)


def _answer_news(question):
    if not any(word in question for word in ["новост", "обновлен", "стать"]):
        return None

    news_items = News.objects.filter(is_published=True).order_by("-published_at")[:5]
    if not news_items:
        return "Опубликованных новостей пока нет."

    lines = [
        f"{item.title} — {item.published_at:%d.%m.%Y}. {item.summary}"
        for item in news_items
    ]
    return "Последние новости:\n" + "\n".join(f"• {line}" for line in lines)


def _answer_delivery_payment(question):
    if any(word in question for word in ["достав", "курьер"]):
        choices = ", ".join(f"{label} — {_format_money(Order.DELIVERY_COST[key])}" for key, label in Order.DELIVERY_CHOICES)
        return f"Доступные способы доставки: {choices}. Статус доставки можно смотреть в личном кабинете."

    if any(word in question for word in ["оплат", "платеж", "карт", "налич"]):
        choices = ", ".join(label for _, label in Order.PAYMENT_CHOICES)
        return f"Доступные способы оплаты: {choices}."

    return None


def _build_qna_answer(request, question):
    normalized_question = _normalize_question(question)
    if not normalized_question:
        return "Напишите вопрос о товарах, заказах, доставке, оплате, акциях, новостях или отзывах."

    handlers = [
        _answer_orders,
        _answer_cart,
        lambda req, text: _answer_delivery_payment(text),
        lambda req, text: _answer_sales(text),
        lambda req, text: _answer_reviews(text),
        lambda req, text: _answer_news(text),
        lambda req, text: _answer_catalog(text),
        lambda req, text: _answer_products(text),
    ]

    for handler in handlers:
        answer = handler(request, normalized_question)
        if answer:
            return answer

    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    latest_news = News.objects.filter(is_published=True).count()

    return (
        "Я отвечаю по данным магазина. Можно спросить, например: "
        "\"есть ли iPhone в наличии\", \"какие есть скидки\", "
        "\"мой последний заказ\", \"что в корзине\", \"последние новости\".\n"
        f"Сейчас в базе: товаров {total_products}, категорий {total_categories}, новостей {latest_news}."
    )


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


@require_POST
def qna_ask(request):
    question = request.POST.get("question", "")
    answer = _build_qna_answer(request, question)
    return JsonResponse({"answer": answer})
