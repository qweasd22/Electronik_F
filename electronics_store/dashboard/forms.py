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