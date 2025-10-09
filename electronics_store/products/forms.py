from django import forms
from .models import Category, Brand

class ProductFilterForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, empty_label="Все категории")
    brand = forms.ModelChoiceField(queryset=Brand.objects.all(), required=False, empty_label="Все бренды")
    min_price = forms.DecimalField(required=False, decimal_places=2, max_digits=10, label="Мин. цена")
    max_price = forms.DecimalField(required=False, decimal_places=2, max_digits=10, label="Макс. цена")
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Поиск по названию', 'class': 'form-control'}), label='Поиск')

from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'placeholder': 'Напишите ваш отзыв...', 'rows': 3}),
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)], attrs={'class': 'form-control'}),
        }
