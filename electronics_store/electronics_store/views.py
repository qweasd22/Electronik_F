import json
import re
from functools import lru_cache

from django.db.models import Avg, Count
from django.db.models.functions import Coalesce
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from orders.models import CartItem, Order
from products.models import Brand, Category, Product, Review, Sale
from news.models import News
from .forms import ContactForm


DEFAULT_QNA_TRAINING = {
    "suggestions": [
        "Какие есть скидки?",
        "Есть ли Samsung в наличии?",
        "Сколько стоит iPhone?",
        "Что у меня в корзине?",
        "Мой последний заказ",
        "Какие бренды есть?",
    ],
    "empty_answer": "Напишите вопрос о товарах, заказах, доставке, оплате, акциях, новостях или отзывах.",
    "product_clarification": (
        "Уточните, пожалуйста, товар, бренд или категорию. Например: "
        "\"есть ли Samsung в наличии\", \"цена iPhone\", \"ноутбук MSI\"."
    ),
    "fallback_answer": (
        "Я отвечаю по данным магазина, но не смог точно определить вопрос. "
        "Попробуйте спросить про конкретный товар, бренд, категорию, скидки, корзину, заказ, доставку или оплату."
    ),
    "stop_words": [
        "а", "в", "во", "где", "да", "для", "до", "его", "ее", "есть", "и", "из", "или", "как", "какая",
        "какие", "какой", "когда", "ли", "мне", "мой", "моя", "мои", "можно", "на", "найди", "о", "об",
        "от", "покажи", "по", "подскажи", "про", "с", "со", "сколько", "стоит", "у", "что", "это",
        "товар", "товара", "товары", "магазин", "наличие", "наличии", "наличия",
        "акции", "акция", "доставка", "доставки", "заказ", "корзина", "оплата", "оплаты", "отзыв",
        "отзыва", "отзывы", "оценка", "оценки", "рейтинг", "рейтинга", "скидка", "скидки", "цена",
        "цену", "цены", "стоимость", "стоимости",
    ],
    "generic_product_words": [
        "белый", "беспроводная", "беспроводной", "гб", "дюйм", "монитор", "ноутбук", "пк", "проводная",
        "проводной", "розовый", "серебристый", "смартфон", "телевизор", "телефон", "черный",
    ],
    "intents": [
        {
            "name": "checkout",
            "handler": "checkout",
            "priority": 95,
            "phrases": ["как оформить заказ", "оформить заказ", "как заказать", "купить товар"],
            "keywords": ["оформ", "заказать", "купить"],
        },
        {
            "name": "orders",
            "handler": "orders",
            "priority": 90,
            "phrases": ["мой заказ", "последний заказ", "статус заказа", "где заказ"],
            "keywords": ["заказ", "статус", "трек"],
        },
        {
            "name": "cart",
            "handler": "cart",
            "priority": 90,
            "phrases": ["что в корзине", "моя корзина", "корзина"],
            "keywords": ["корзин", "cart"],
        },
        {
            "name": "sales",
            "handler": "sales",
            "priority": 88,
            "phrases": ["какие есть скидки", "активные акции", "товары со скидкой"],
            "keywords": ["скид", "акци", "распрод", "дешев"],
        },
        {
            "name": "product_stock",
            "handler": "products",
            "priority": 82,
            "phrases": ["есть ли", "в наличии", "сколько осталось"],
            "keywords": ["склад", "остал"],
            "requires_catalog_entity": True,
        },
        {
            "name": "product_price",
            "handler": "products",
            "priority": 80,
            "phrases": ["сколько стоит", "какая цена", "цена"],
            "keywords": ["цен", "стоим"],
            "requires_catalog_entity": True,
        },
        {
            "name": "delivery",
            "handler": "delivery",
            "priority": 78,
            "phrases": ["способы доставки", "стоимость доставки", "курьерская доставка"],
            "keywords": ["достав", "курьер", "получ"],
        },
        {
            "name": "payment",
            "handler": "payment",
            "priority": 78,
            "phrases": ["способы оплаты", "как оплатить", "оплата заказа"],
            "keywords": ["оплат", "платеж", "карт", "налич"],
        },
        {
            "name": "reviews",
            "handler": "reviews",
            "priority": 75,
            "phrases": ["отзывы", "рейтинг товара", "оценка товара"],
            "keywords": ["отзыв", "рейтинг", "оцен", "звезд"],
        },
        {
            "name": "news",
            "handler": "news",
            "priority": 72,
            "phrases": ["последние новости", "новости магазина"],
            "keywords": ["новост", "стать", "публикац", "обновлен"],
        },
        {
            "name": "brands",
            "handler": "brands",
            "priority": 70,
            "phrases": ["какие бренды", "список брендов"],
            "keywords": ["бренд", "марка", "производител"],
        },
        {
            "name": "categories",
            "handler": "categories",
            "priority": 70,
            "phrases": ["какие категории", "разделы каталога"],
            "keywords": ["категор", "раздел"],
        },
        {
            "name": "product_search",
            "handler": "products",
            "priority": 55,
            "phrases": ["найди товар", "покажи товар", "подбери товар"],
            "keywords": ["товар", "каталог", "модель"],
            "requires_catalog_entity": True,
        },
    ],
}


def _normalize_question(question):
    return " ".join(question.lower().strip().split())


@lru_cache(maxsize=1)
def _load_qna_training():
    training_path = getattr(
        settings,
        "QNA_TRAINING_FILE",
        settings.BASE_DIR / "electronics_store" / "qna_training.json",
    )

    try:
        with open(training_path, "r", encoding="utf-8") as file:
            file_training = json.load(file)
    except (OSError, ValueError, TypeError):
        file_training = {}

    training = dict(DEFAULT_QNA_TRAINING)
    if isinstance(file_training, dict):
        for key, value in file_training.items():
            if value:
                training[key] = value

    return training


def _qna_words(text):
    return re.findall(r"[a-zа-яё0-9]+", _normalize_question(text))


def _qna_keyword_match(question, keyword):
    keyword = _normalize_question(keyword)
    if not keyword:
        return False

    if " " in keyword:
        return keyword in question

    for word in _qna_words(question):
        if (
            word == keyword
            or (len(keyword) >= 3 and word.startswith(keyword))
            or (len(word) >= 4 and keyword.startswith(word))
            or (len(keyword) >= 3 and keyword in word)
        ):
            return True

    return False


def _important_question_tokens(question, include_generic=False):
    training = _load_qna_training()
    stop_words = set(training.get("stop_words", []))
    generic_words = set(training.get("generic_product_words", []))
    tokens = []

    for token in _qna_words(question):
        if len(token) < 2 or token in stop_words:
            continue
        if not include_generic and token in generic_words:
            continue
        tokens.append(token)

    return tokens


def _entity_token_set(items):
    tokens = set()
    for item in items:
        tokens.update(_important_question_tokens(item.name, include_generic=True))
    return tokens


def _match_named_objects(model, question):
    matches = []
    normalized_question = _normalize_question(question)

    for item in model.objects.all():
        normalized_name = _normalize_question(item.name)
        if not normalized_name:
            continue

        if normalized_name in normalized_question:
            matches.append((100 + len(normalized_name), item))
            continue

        name_words = _important_question_tokens(item.name, include_generic=True)
        hit_count = sum(1 for word in name_words if _qna_keyword_match(normalized_question, word))
        if hit_count:
            matches.append((hit_count * 10 + len(normalized_name), item))

    matches.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in matches]


def _token_hits_text(token, text):
    normalized_text = _normalize_question(text)
    if token in normalized_text:
        return True

    for word in _qna_words(normalized_text):
        if word == token or word.startswith(token) or token.startswith(word):
            return True

    return False


def _score_products(products, tokens):
    if not tokens:
        return list(products[:5])

    scored_products = []
    for product in products:
        name = _normalize_question(product.name)
        hits = [token for token in tokens if _token_hits_text(token, name)]
        if not hits:
            continue

        if len(tokens) > 1 and len(hits) < min(2, len(tokens)):
            continue

        scored_products.append((len(hits) * 20 + product.stock, product))

    scored_products.sort(key=lambda pair: pair[0], reverse=True)
    return [product for _, product in scored_products[:5]]


def _catalog_context(question):
    brands = _match_named_objects(Brand, question)
    categories = _match_named_objects(Category, question)
    entity_tokens = _entity_token_set(brands + categories)
    tokens = [
        token for token in _important_question_tokens(question)
        if token not in entity_tokens
    ]

    return {
        "brands": brands,
        "categories": categories,
        "tokens": tokens,
    }


def _has_catalog_entity(question):
    context = _catalog_context(question)
    return bool(context["brands"] or context["categories"] or _find_products(question))


def _detect_qna_intent(question):
    best_match = None
    best_score = 0

    for intent in _load_qna_training().get("intents", []):
        phrases = intent.get("phrases", [])
        keywords = intent.get("keywords", [])
        phrase_hits = sum(1 for phrase in phrases if _qna_keyword_match(question, phrase))
        keyword_hits = sum(1 for keyword in keywords if _qna_keyword_match(question, keyword))

        if not phrase_hits and not keyword_hits:
            continue

        score = int(intent.get("priority", 0)) + phrase_hits * 30 + keyword_hits * 8
        if score > best_score:
            best_score = score
            best_match = intent

    return best_match


def _format_money(value):
    return f"{value} ₽"


def _qna_link(title, url, description=""):
    return {
        "title": title,
        "url": url,
        "description": description,
    }


def _qna_response(answer, links=None, suggestions=None):
    return {
        "answer": answer,
        "links": links or [],
        "suggestions": suggestions or _qna_suggestions(),
    }


def _qna_suggestions():
    return _load_qna_training().get("suggestions") or DEFAULT_QNA_TRAINING["suggestions"]


def _find_products(question):
    question = _normalize_question(question)
    context = _catalog_context(question)
    products = Product.objects.select_related("category", "brand").prefetch_related("sales")

    if context["brands"]:
        products = products.filter(brand__in=context["brands"])
    if context["categories"]:
        products = products.filter(category__in=context["categories"])

    product_list = list(products[:80])

    if context["tokens"]:
        scored_products = _score_products(product_list, context["tokens"])
        if scored_products:
            return scored_products

    if context["brands"] or context["categories"]:
        return product_list[:5]

    tokens = _important_question_tokens(question)
    if not tokens:
        return []

    return _score_products(product_list, tokens)


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


def _answer_products(question, clarify=False):
    products = _find_products(question)[:5]
    if not products:
        if clarify:
            return _qna_response(
                _load_qna_training().get("product_clarification", DEFAULT_QNA_TRAINING["product_clarification"]),
                links=[_qna_link("Открыть каталог", reverse("products:product_list"), "Можно выбрать товар вручную.")],
            )
        return None

    lines = [_product_line(product) for product in products]
    links = [
        _qna_link(
            product.name,
            reverse("products:product_detail", args=[product.id]),
            f"{_format_money(product.get_discounted_price())}, {product.stock} шт. в наличии",
        )
        for product in products
    ]
    return _qna_response(
        "Нашёл подходящие товары:\n" + "\n".join(f"• {line}" for line in lines),
        links=links,
    )


def _answer_orders(request, question):
    if not any(word in question for word in ["заказ", "статус"]):
        return None

    if not request.user.is_authenticated:
        return _qna_response(
            "По заказам могу ответить после входа в аккаунт.",
            links=[_qna_link("Войти в аккаунт", reverse("accounts:login"), "После входа покажу ваши заказы.")],
        )

    order_id_match = re.search(r"\b\d+\b", question)
    orders = Order.objects.filter(user=request.user).prefetch_related("items__product")

    if order_id_match:
        order = orders.filter(id=int(order_id_match.group())).first()
        if not order:
            return _qna_response("У вас не найден заказ с таким номером.")

        paid_text = "оплачен" if order.is_paid else "не оплачен"
        return _qna_response(
            (
                f"Заказ #{order.id}: {order.get_status_display()}, {paid_text}. "
                f"Доставка: {order.get_delivery_method_display()}, адрес: {order.address}. "
                f"Сумма: {_format_money(order.total_price)}."
            ),
            links=[
                _qna_link(
                    f"Открыть заказ #{order.id}",
                    reverse("orders:order_detail", args=[order.id]),
                    "Детали заказа и состав покупки",
                )
            ],
        )

    recent_orders = list(orders.order_by("-created_at")[:3])
    if not recent_orders:
        return _qna_response(
            "У вас пока нет заказов.",
            links=[_qna_link("Перейти в каталог", reverse("products:product_list"), "Выберите первый товар.")],
        )

    lines = [
        f"#{order.id}: {order.get_status_display()}, сумма {_format_money(order.total_price)}, "
        f"создан {order.created_at:%d.%m.%Y}"
        for order in recent_orders
    ]
    links = [
        _qna_link(
            f"Заказ #{order.id}",
            reverse("orders:order_detail", args=[order.id]),
            f"{order.get_status_display()}, {_format_money(order.total_price)}",
        )
        for order in recent_orders
    ]
    return _qna_response(
        "Ваши последние заказы:\n" + "\n".join(f"• {line}" for line in lines),
        links=links,
    )


def _answer_cart(request, question):
    if not any(word in question for word in ["корзин", "cart"]):
        return None

    if not request.user.is_authenticated:
        return _qna_response(
            "Корзина доступна после входа в аккаунт.",
            links=[_qna_link("Войти в аккаунт", reverse("accounts:login"), "После входа покажу содержимое корзины.")],
        )

    cart_items = (
        CartItem.objects
        .filter(user=request.user)
        .select_related("product")
        .order_by("product__name")
    )

    if not cart_items:
        return _qna_response(
            "Ваша корзина сейчас пуста.",
            links=[_qna_link("Перейти в каталог", reverse("products:product_list"), "Посмотреть товары.")],
        )

    total_quantity = sum(item.quantity for item in cart_items)
    total_price = sum((item.total_price for item in cart_items), start=0)
    lines = [
        f"{item.product.name} — {item.quantity} шт., {_format_money(item.total_price)}"
        for item in cart_items[:5]
    ]

    return _qna_response(
        (
            f"В корзине {total_quantity} шт. товаров на сумму {_format_money(total_price)}:\n"
            + "\n".join(f"• {line}" for line in lines)
        ),
        links=[
            _qna_link("Открыть корзину", reverse("orders:cart"), "Проверить товары и количество"),
            _qna_link("Оформить заказ", reverse("orders:checkout"), "Перейти к оформлению"),
        ],
    )


def _answer_checkout(request):
    links = [
        _qna_link("Каталог", reverse("products:product_list"), "Выберите товар и добавьте его в корзину."),
    ]

    if request.user.is_authenticated:
        links.extend([
            _qna_link("Корзина", reverse("orders:cart"), "Проверьте товары перед оформлением."),
            _qna_link("Оформить заказ", reverse("orders:checkout"), "Перейти к выбору доставки и оплаты."),
        ])
        account_text = "После оформления заказ появится в личном кабинете."
    else:
        links.append(_qna_link("Войти в аккаунт", reverse("accounts:login"), "После входа можно оформить заказ."))
        account_text = "Для оформления заказа нужно войти в аккаунт."

    return _qna_response(
        (
            "Чтобы оформить заказ: выберите товар в каталоге, добавьте его в корзину, "
            "проверьте количество, затем перейдите к оформлению и выберите доставку с оплатой. "
            f"{account_text}"
        ),
        links=links,
    )


def _answer_catalog(question, section=None):
    if section == "categories" or "категор" in question:
        categories = Category.objects.annotate(product_count=Count("products")).order_by("name")[:8]
        if categories:
            lines = [f"{category.name} ({category.product_count})" for category in categories]
            return _qna_response(
                "Категории товаров:\n" + "\n".join(f"• {line}" for line in lines),
                links=[_qna_link("Открыть каталог", reverse("products:product_list"), "Фильтры по категориям доступны в каталоге")],
            )

    if section == "brands" or "бренд" in question or "brand" in question:
        brands = Brand.objects.annotate(product_count=Count("products")).order_by("name")[:8]
        if brands:
            lines = [f"{brand.name} ({brand.product_count})" for brand in brands]
            return _qna_response(
                "Бренды в каталоге:\n" + "\n".join(f"• {line}" for line in lines),
                links=[_qna_link("Открыть каталог", reverse("products:product_list"), "Фильтры по брендам доступны в каталоге")],
            )

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
            return _qna_response(
                "Сейчас активных скидок не найдено.",
                links=[_qna_link("Посмотреть каталог", reverse("products:product_list"), "Все товары магазина")],
            )

        lines = [
            f"{product.name}: {_format_money(product.get_discounted_price())} вместо {_format_money(product.price)}"
            for product in discounted_products
        ]
        return _qna_response(
            "Товары со скидкой:\n" + "\n".join(f"• {line}" for line in lines),
            links=[
                _qna_link(
                    product.name,
                    reverse("products:product_detail", args=[product.id]),
                    f"{_format_money(product.get_discounted_price())} вместо {_format_money(product.price)}",
                )
                for product in discounted_products
            ],
        )

    lines = [
        f"{sale.name}: скидка {sale.discount_percentage}%, товаров: {sale.products.count()}"
        for sale in active_sales[:5]
    ]
    sale_products = []
    for sale in active_sales[:3]:
        sale_products.extend(list(sale.products.all()[:2]))

    links = [
        _qna_link(
            product.name,
            reverse("products:product_detail", args=[product.id]),
            f"Цена со скидкой {_format_money(product.get_discounted_price())}",
        )
        for product in sale_products[:5]
    ]
    if not links:
        links = [_qna_link("Открыть каталог", reverse("products:product_list"), "Посмотреть товары магазина")]

    return _qna_response(
        "Активные акции:\n" + "\n".join(f"• {line}" for line in lines),
        links=links,
    )


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
        return _qna_response(
            "Информация по отзывам:\n" + "\n".join(f"• {line}" for line in lines),
            links=[
                _qna_link(
                    product.name,
                    reverse("products:product_detail", args=[product.id]),
                    f"Рейтинг {product.average_rating()}",
                )
                for product in products
            ],
        )

    reviewed_products = (
        Product.objects
        .annotate(avg_rating=Coalesce(Avg("ratings__stars"), 0.0))
        .order_by("-avg_rating", "-id")[:5]
    )
    lines = [f"{product.name}: рейтинг {product.avg_rating:.1f}" for product in reviewed_products]
    return _qna_response(
        "Самые рейтинговые товары:\n" + "\n".join(f"• {line}" for line in lines),
        links=[
            _qna_link(
                product.name,
                reverse("products:product_detail", args=[product.id]),
                f"Рейтинг {product.avg_rating:.1f}",
            )
            for product in reviewed_products
        ],
    )


def _answer_news(question):
    if not any(word in question for word in ["новост", "обновлен", "стать"]):
        return None

    news_items = News.objects.filter(is_published=True).order_by("-published_at")[:5]
    if not news_items:
        return _qna_response("Опубликованных новостей пока нет.")

    lines = [
        f"{item.title} — {item.published_at:%d.%m.%Y}. {item.summary}"
        for item in news_items
    ]
    return _qna_response(
        "Последние новости:\n" + "\n".join(f"• {line}" for line in lines),
        links=[
            _qna_link(
                item.title,
                reverse("news:news_detail", kwargs={"pk": item.id}),
                item.published_at.strftime("%d.%m.%Y"),
            )
            for item in news_items
        ],
    )


def _answer_delivery_payment(question):
    if any(word in question for word in ["достав", "курьер"]):
        choices = ", ".join(f"{label} — {_format_money(Order.DELIVERY_COST[key])}" for key, label in Order.DELIVERY_CHOICES)
        return _qna_response(
            f"Доступные способы доставки: {choices}. Статус доставки можно смотреть в личном кабинете.",
            links=[
                _qna_link("Личный кабинет", reverse("accounts:profile"), "Ваши заказы и статусы"),
                _qna_link("Оформление заказа", reverse("orders:checkout"), "Выбор доставки при оформлении"),
            ],
        )

    if any(word in question for word in ["оплат", "платеж", "карт", "налич"]):
        choices = ", ".join(label for _, label in Order.PAYMENT_CHOICES)
        return _qna_response(
            f"Доступные способы оплаты: {choices}.",
            links=[_qna_link("Оформить заказ", reverse("orders:checkout"), "Выбрать способ оплаты")],
        )

    return None


def _dispatch_qna_intent(request, question, intent):
    if not intent:
        return None

    handler = intent.get("handler")
    if intent.get("requires_catalog_entity") and not _has_catalog_entity(question):
        return _answer_products(question, clarify=True)

    if handler == "checkout":
        return _answer_checkout(request)
    if handler == "orders":
        return _answer_orders(request, question)
    if handler == "cart":
        return _answer_cart(request, question)
    if handler == "delivery":
        return _answer_delivery_payment(question)
    if handler == "payment":
        return _answer_delivery_payment(question)
    if handler == "sales":
        return _answer_sales(question)
    if handler == "reviews":
        return _answer_reviews(question)
    if handler == "news":
        return _answer_news(question)
    if handler == "brands":
        return _answer_catalog(question, section="brands")
    if handler == "categories":
        return _answer_catalog(question, section="categories")
    if handler == "products":
        return _answer_products(question, clarify=True)

    return None


def _build_qna_answer(request, question):
    normalized_question = _normalize_question(question)
    training = _load_qna_training()
    if not normalized_question:
        return _qna_response(training.get("empty_answer", DEFAULT_QNA_TRAINING["empty_answer"]))

    intent = _detect_qna_intent(normalized_question)
    answer = _dispatch_qna_intent(request, normalized_question, intent)
    if answer:
        return answer

    product_answer = _answer_products(normalized_question)
    if product_answer:
        return product_answer

    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    latest_news = News.objects.filter(is_published=True).count()

    return _qna_response(
        (
            f"{training.get('fallback_answer', DEFAULT_QNA_TRAINING['fallback_answer'])}\n"
            f"Сейчас в базе: товаров {total_products}, категорий {total_categories}, новостей {latest_news}."
        ),
        links=[
            _qna_link("Каталог", reverse("products:product_list"), "Товары, цены, наличие и фильтры"),
            _qna_link("Новости", reverse("news:news_list"), "Последние публикации магазина"),
        ],
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
    payload = _build_qna_answer(request, question)
    if isinstance(payload, str):
        payload = _qna_response(payload)

    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        messages.info(request, payload.get("answer", "Ответ не найден."))
        return redirect(request.META.get("HTTP_REFERER") or "home")

    return JsonResponse(payload)
