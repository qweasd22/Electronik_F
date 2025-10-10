from django.contrib import admin
from .models import CartItem, Order, OrderItem

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'total_price')
    search_fields = ('user__username', 'product__name')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'price_at_purchase', 'total_price')

    def total_price(self, obj):
        return obj.total_price  # Используйте метод total_price
    total_price.short_description = 'Общая цена'

    def save_model(self, request, obj, form, change):
        if obj.quantity is None:
            obj.quantity = 1  # Значение по умолчанию
        if obj.price_at_purchase is None:
            obj.price_at_purchase = 0  # Значение по умолчанию

        super().save_model(request, obj, form, change)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'price_at_purchase', 'total_price')
    readonly_fields = ('total_price',)

class OrderAdmin(admin.ModelAdmin):
    # Список отображаемых полей на главной странице заказов
    list_display = ('id', 'user', 'created_at', 'status', 'is_paid', 'total_price', 'delivery_method', 'address')
    
    # Фильтры для поиска
    list_filter = ('status', 'is_paid', 'delivery_method')
    
    # Поиск по полям
    search_fields = ('user__username', 'address')
    
    # Сортировка заказов по дате
    ordering = ('-created_at',)
    
    # Включаем возможность редактировать товары в заказе
    inlines = [OrderItemInline]

    # Параметры для редактирования заказов
    fields = ('user', 'created_at', 'status', 'is_paid', 'address', 'delivery_method')
    
    # Указываем, что поле created_at только для чтения
    readonly_fields = ('created_at',)  

    # Сохранение модели, в случае нового заказа устанавливаем статус "processing"
    def save_model(self, request, obj, form, change):
        if not change:  # Если это новый заказ
            obj.status = 'processing'  # Устанавливаем статус по умолчанию
        super().save_model(request, obj, form, change)

admin.site.register(Order, OrderAdmin)


from django.contrib import admin
from .models import SaleEvent

class SaleEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'order_id', 'product', 'quantity', 'total_price', 'timestamp')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('user__username', 'product__name', 'order_id')

admin.site.register(SaleEvent, SaleEventAdmin)


