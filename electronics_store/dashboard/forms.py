from django import forms

from orders.models import Order


class DashboardOrderStatusForm(forms.Form):
    status = forms.ChoiceField(
        label="Новый статус",
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    note = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "dashboard-textarea",
                "rows": 4,
                "placeholder": "Комментарий к изменению статуса",
            }
        ),
    )

from django import forms

from orders.models import Order
from products.models import Product, Category, Brand, Sale


class DashboardOrderStatusForm(forms.Form):
    status = forms.ChoiceField(
        label="Новый статус",
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    note = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "dashboard-textarea",
                "rows": 4,
                "placeholder": "Комментарий к изменению статуса",
            }
        ),
    )


class DashboardProductForm(forms.ModelForm):
    sales = forms.ModelMultipleChoiceField(
        label="Скидки",
        queryset=Sale.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "brand",
            "description",
            "price",
            "stock",
            "image",
            "sales",
            "additional_info",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "dashboard-input"}),
            "slug": forms.TextInput(attrs={"class": "dashboard-input"}),
            "category": forms.Select(attrs={"class": "dashboard-select"}),
            "brand": forms.Select(attrs={"class": "dashboard-select"}),
            "description": forms.Textarea(attrs={"class": "dashboard-textarea", "rows": 5}),
            "price": forms.NumberInput(attrs={"class": "dashboard-input", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "dashboard-input", "min": "0"}),
            "image": forms.ClearableFileInput(attrs={"class": "dashboard-input"}),
            "additional_info": forms.Textarea(attrs={"class": "dashboard-textarea", "rows": 5}),
        }


class DashboardProductFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Поиск",
        widget=forms.TextInput(
            attrs={
                "class": "dashboard-input",
                "placeholder": "Название, slug, описание",
            }
        ),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Все категории",
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        empty_label="Все бренды",
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    stock_state = forms.ChoiceField(
        required=False,
        label="Остаток",
        choices=[
            ("", "Все"),
            ("in_stock", "В наличии"),
            ("low_stock", "Мало на складе"),
            ("out_of_stock", "Нет в наличии"),
        ],
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )

from django import forms
from django.contrib.auth import get_user_model

from orders.models import Order
from products.models import Product, Category, Brand, Sale

User = get_user_model()


class DashboardOrderStatusForm(forms.Form):
    status = forms.ChoiceField(
        label="Новый статус",
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    note = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "dashboard-textarea",
                "rows": 4,
                "placeholder": "Комментарий к изменению статуса",
            }
        ),
    )


class DashboardProductForm(forms.ModelForm):
    sales = forms.ModelMultipleChoiceField(
        label="Скидки",
        queryset=Sale.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "brand",
            "description",
            "price",
            "stock",
            "image",
            "sales",
            "additional_info",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "dashboard-input"}),
            "slug": forms.TextInput(attrs={"class": "dashboard-input"}),
            "category": forms.Select(attrs={"class": "dashboard-select"}),
            "brand": forms.Select(attrs={"class": "dashboard-select"}),
            "description": forms.Textarea(attrs={"class": "dashboard-textarea", "rows": 5}),
            "price": forms.NumberInput(attrs={"class": "dashboard-input", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "dashboard-input", "min": "0"}),
            "image": forms.ClearableFileInput(attrs={"class": "dashboard-input"}),
            "additional_info": forms.Textarea(attrs={"class": "dashboard-textarea", "rows": 5}),
        }


class DashboardProductFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Поиск",
        widget=forms.TextInput(
            attrs={
                "class": "dashboard-input",
                "placeholder": "Название, slug, описание",
            }
        ),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Все категории",
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        empty_label="Все бренды",
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    stock_state = forms.ChoiceField(
        required=False,
        label="Остаток",
        choices=[
            ("", "Все"),
            ("in_stock", "В наличии"),
            ("low_stock", "Мало на складе"),
            ("out_of_stock", "Нет в наличии"),
        ],
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )


class DashboardUserFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Поиск",
        widget=forms.TextInput(
            attrs={
                "class": "dashboard-input",
                "placeholder": "Логин, email, имя, телефон",
            }
        ),
    )
    is_active = forms.ChoiceField(
        required=False,
        label="Активность",
        choices=[
            ("", "Все"),
            ("yes", "Активные"),
            ("no", "Неактивные"),
        ],
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    is_staff = forms.ChoiceField(
        required=False,
        label="Staff",
        choices=[
            ("", "Все"),
            ("yes", "Да"),
            ("no", "Нет"),
        ],
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    is_superuser = forms.ChoiceField(
        required=False,
        label="Superuser",
        choices=[
            ("", "Все"),
            ("yes", "Да"),
            ("no", "Нет"),
        ],
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )


class DashboardUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "birth_date",
            "address",
            "is_active",
            "is_staff",
            "is_superuser",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "dashboard-input"}),
            "email": forms.EmailInput(attrs={"class": "dashboard-input"}),
            "first_name": forms.TextInput(attrs={"class": "dashboard-input"}),
            "last_name": forms.TextInput(attrs={"class": "dashboard-input"}),
            "phone_number": forms.TextInput(attrs={"class": "dashboard-input"}),
            "birth_date": forms.DateInput(attrs={"class": "dashboard-input", "type": "date"}),
            "address": forms.Textarea(attrs={"class": "dashboard-textarea", "rows": 4}),
        }

from news.models import News, Category as NewsCategory
class DashboardNewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = [
            "title",
            "summary",
            "content",
            "published_at",
            "category",
            "image",
            "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "dashboard-input"}),
            "summary": forms.Textarea(attrs={"class": "dashboard-textarea", "rows": 3}),
            "content": forms.Textarea(attrs={"class": "dashboard-textarea", "rows": 10}),
            "published_at": forms.DateTimeInput(
                attrs={"class": "dashboard-input", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "category": forms.Select(attrs={"class": "dashboard-select"}),
            "image": forms.ClearableFileInput(attrs={"class": "dashboard-input"}),
            "is_published": forms.CheckboxInput(attrs={"class": "dashboard-checkbox"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = NewsCategory.objects.all().order_by("name")

        if self.instance and self.instance.pk and self.instance.published_at:
            self.initial["published_at"] = self.instance.published_at.strftime("%Y-%m-%dT%H:%M")


class DashboardNewsFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Поиск",
        widget=forms.TextInput(
            attrs={
                "class": "dashboard-input",
                "placeholder": "Заголовок, описание, текст",
            }
        ),
    )
    category = forms.ModelChoiceField(
        queryset=NewsCategory.objects.all().order_by("name"),
        required=False,
        empty_label="Все категории",
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    is_published = forms.ChoiceField(
        required=False,
        label="Статус",
        choices=[
            ("", "Все"),
            ("yes", "Опубликовано"),
            ("no", "Черновики"),
        ],
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )

class DashboardSaleForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(
        label="Товары со скидкой",
        queryset=Product.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Sale
        fields = [
            "name",
            "discount_percentage",
            "start_date",
            "end_date",
            "is_active",
            "products",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "dashboard-input"}),
            "discount_percentage": forms.NumberInput(
                attrs={"class": "dashboard-input", "step": "0.01", "min": "0", "max": "100"}
            ),
            "start_date": forms.DateTimeInput(
                attrs={"class": "dashboard-input", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_date": forms.DateTimeInput(
                attrs={"class": "dashboard-input", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "is_active": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields["products"].initial = self.instance.products.all()

        if self.instance.pk and self.instance.start_date:
            self.initial["start_date"] = self.instance.start_date.strftime("%Y-%m-%dT%H:%M")

        if self.instance.pk and self.instance.end_date:
            self.initial["end_date"] = self.instance.end_date.strftime("%Y-%m-%dT%H:%M")

    def clean_discount_percentage(self):
        value = self.cleaned_data["discount_percentage"]
        if value <= 0 or value > 100:
            raise forms.ValidationError("Скидка должна быть больше 0 и не больше 100%.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if end_date and start_date and end_date < start_date:
            self.add_error("end_date", "Дата окончания не может быть раньше даты начала.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=commit)

        def save_m2m_products():
            instance.products.set(self.cleaned_data["products"])

        if commit:
            save_m2m_products()
        else:
            self._save_m2m_products = save_m2m_products

        return instance


class DashboardSaleFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Поиск",
        widget=forms.TextInput(
            attrs={
                "class": "dashboard-input",
                "placeholder": "Название скидки",
            }
        ),
    )
    is_active = forms.ChoiceField(
        required=False,
        label="Активность",
        choices=[
            ("", "Все"),
            ("yes", "Активные"),
            ("no", "Неактивные"),
        ],
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )
    current_state = forms.ChoiceField(
        required=False,
        label="Состояние по дате",
        choices=[
            ("", "Все"),
            ("current", "Действует сейчас"),
            ("upcoming", "Будущие"),
            ("expired", "Завершённые"),
        ],
        widget=forms.Select(attrs={"class": "dashboard-select"}),
    )