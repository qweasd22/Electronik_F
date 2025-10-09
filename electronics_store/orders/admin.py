from django.contrib import admin
from .models import CartItem, Order, OrderItem

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'total_price')
    search_fields = ('user__username', 'product__name')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'total_price')
    search_fields = ('order__id', 'product__name')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'quantity', 'total_price')
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'delivery_method', 'is_paid', 'total_price')
    list_filter = ('is_paid', 'delivery_method', 'created_at')
    search_fields = ('user__username', 'id')
    inlines = [OrderItemInline]
    actions = ['mark_as_paid']

    def mark_as_paid(self, request, queryset):
        queryset.update(is_paid=True)
        self.message_user(request, "Выбранные заказы отмечены как оплаченные.")
    mark_as_paid.short_description = "Отметить выбранные заказы как оплаченные"
