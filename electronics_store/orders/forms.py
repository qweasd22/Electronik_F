from django import forms

from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "recipient_name",
            "phone_number",
            "address",
            "delivery_method",
            "payment_method",
            "comment",
        ]
        widgets = {
            "recipient_name": forms.TextInput(
                attrs={"class": "checkout-input", "placeholder": "ФИО получателя"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "checkout-input", "placeholder": "Телефон из 11 цифр"}
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "checkout-input",
                    "rows": 3,
                    "placeholder": "Адрес доставки",
                }
            ),
            "delivery_method": forms.Select(attrs={"class": "checkout-input"}),
            "payment_method": forms.Select(attrs={"class": "checkout-input"}),
            "comment": forms.Textarea(
                attrs={
                    "class": "checkout-input",
                    "rows": 3,
                    "placeholder": "Комментарий к заказу",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_bound and user is not None:
            full_name = f"{user.first_name} {user.last_name}".strip()
            self.fields["recipient_name"].initial = full_name or user.username
            self.fields["phone_number"].initial = getattr(user, "phone_number", "") or ""

    def clean_phone_number(self):
        phone_number = (self.cleaned_data.get("phone_number") or "").strip()

        if not phone_number:
            raise forms.ValidationError("Укажите номер телефона.")

        if not phone_number.isdigit():
            raise forms.ValidationError("Телефон должен содержать только цифры.")

        if len(phone_number) != 11:
            raise forms.ValidationError("Телефон должен содержать ровно 11 цифр.")

        return phone_number