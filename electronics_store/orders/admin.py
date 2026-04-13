from django.contrib import admin
from .models import CartItem, Order, OrderItem, SaleEvent


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'total_price')
    list_filter = ('user',)
    search_fields = ('user__username', 'product__name')
    ordering = ('id',)

    @admin.display(description='Общая цена')
    def total_price(self, obj):
        return obj.total_price


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price_at_purchase', 'total_price')
    search_fields = ('order__id', 'product__name')
    ordering = ('id',)

    @admin.display(description='Общая цена')
    def total_price(self, obj):
        return obj.total_price

    def save_model(self, request, obj, form, change):
        if obj.quantity is None:
            obj.quantity = 1
        if obj.price_at_purchase is None:
            obj.price_at_purchase = 0
        super().save_model(request, obj, form, change)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'price_at_purchase', 'total_price')
    readonly_fields = ('total_price',)

    @admin.display(description='Общая цена')
    def total_price(self, obj):
        return obj.total_price


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'created_at',
        'status',
        'is_paid',
        'total_price',
        'delivery_method',
        'address',
    )
    list_filter = ('status', 'is_paid', 'delivery_method', 'created_at')
    search_fields = ('user__username', 'address')
    ordering = ('-created_at',)
    inlines = [OrderItemInline]
    fields = ('user', 'created_at', 'status', 'is_paid', 'address', 'delivery_method')
    readonly_fields = ('created_at',)
    list_per_page = 20
    date_hierarchy = 'created_at'

    @admin.display(description='Общая сумма')
    def total_price(self, obj):
        return obj.total_price

    def save_model(self, request, obj, form, change):
        if not change and not obj.status:
            obj.status = 'processing'
        super().save_model(request, obj, form, change)


@admin.register(SaleEvent)
class SaleEventAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'action',
        'order_id',
        'product',
        'quantity',
        'total_price',
        'timestamp',
    )
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('user__username', 'product__name', 'order_id')
    ordering = ('-timestamp',)
    list_per_page = 20
    date_hierarchy = 'timestamp'