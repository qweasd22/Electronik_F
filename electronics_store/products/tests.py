from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Brand, Category, Product


class QnaAnswerTests(TestCase):
    def setUp(self):
        phone_category = Category.objects.create(name="Телефон", slug="phone")
        tv_category = Category.objects.create(name="Телевизор", slug="tv")
        apple = Brand.objects.create(name="Apple")
        samsung = Brand.objects.create(name="Samsung")

        Product.objects.create(
            name="Смартфон Samsung Galaxy A56",
            slug="samsung-galaxy-a56",
            category=phone_category,
            brand=samsung,
            price=Decimal("34500.00"),
            stock=24,
        )
        Product.objects.create(
            name="Телевизор Samsung UE43U8000FUXRU",
            slug="samsung-tv-u8000",
            category=tv_category,
            brand=samsung,
            price=Decimal("41000.00"),
            stock=16,
        )
        Product.objects.create(
            name="Смартфон Apple iPhone 15",
            slug="iphone-15",
            category=phone_category,
            brand=apple,
            price=Decimal("62000.00"),
            stock=42,
        )

    def ask(self, question):
        return self.client.post(
            reverse("qna_ask"),
            {"question": question},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        ).json()

    def test_brand_stock_question_uses_exact_catalog_entity(self):
        payload = self.ask("Есть ли Samsung в наличии?")

        self.assertIn("Samsung Galaxy A56", payload["answer"])
        self.assertIn("Samsung UE43U8000FUXRU", payload["answer"])
        self.assertNotIn("iPhone 15", payload["answer"])

    def test_stock_question_without_entity_asks_to_clarify(self):
        payload = self.ask("Есть ли в наличии?")

        self.assertIn("Уточните", payload["answer"])
        self.assertNotIn("Samsung Galaxy A56", payload["answer"])

    def test_review_question_keeps_product_token(self):
        payload = self.ask("Рейтинг iPhone")

        self.assertIn("iPhone 15", payload["answer"])
        self.assertNotIn("Samsung Galaxy A56", payload["answer"])
