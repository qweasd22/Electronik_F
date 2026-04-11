from django import forms
from .models import Category, Brand, Review, Rating


class ProductFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Все категории"
    )
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        empty_label="Все бренды"
    )
    min_price = forms.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=10,
        label="Мин. цена"
    )
    max_price = forms.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=10,
        label="Макс. цена"
    )
    search = forms.CharField(
        required=False,
        label="Поиск",
        widget=forms.TextInput(attrs={
            "placeholder": "Поиск по названию",
            "class": "form-control"
        })
    )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4}),
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ["stars"]