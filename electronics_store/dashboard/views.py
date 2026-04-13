from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, F, DecimalField
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from orders.models import Order, OrderItem, SaleEvent
from products.models import Product
from .forms import (
    DashboardOrderStatusForm,
    DashboardProductFilterForm,
    DashboardProductForm,
)
from .mixins import DashboardAccessMixin

User = get_user_model()


class DashboardHomeView(DashboardAccessMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_orders = Order.objects.count()
        completed_orders = Order.objects.filter(status='delivered').count()
        paid_orders = Order.objects.filter(is_paid=True).count()
        total_users = User.objects.count()
        total_products = Product.objects.count()
        low_stock_products = Product.objects.filter(stock__lte=5).count()
        delivered_orders = Order.objects.filter(status='delivered').count()

        total_revenue = OrderItem.objects.aggregate(
            total=Sum(
                F('quantity') * F('price_at_purchase'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )['total'] or Decimal('0.00')

        recent_orders = Order.objects.select_related('user', 'courier').order_by('-created_at')[:5]
        recent_users = User.objects.order_by('-date_joined')[:5]
        low_stock_items = Product.objects.filter(stock__lte=5).order_by('stock')[:5]
        recent_sales = SaleEvent.objects.select_related('user', 'product', 'order').order_by('-timestamp')[:5]

        context.update({
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'paid_orders': paid_orders,
            'total_users': total_users,
            'total_products': total_products,
            'low_stock_products': low_stock_products,
            'delivered_orders': delivered_orders,
            'total_revenue': total_revenue,
            'recent_orders': recent_orders,
            'recent_users': recent_users,
            'low_stock_items': low_stock_items,
            'recent_sales': recent_sales,
        })
        return context


class DashboardOrderListView(DashboardAccessMixin, ListView):
    model = Order
    template_name = 'dashboard/orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 15

    def get_queryset(self):
        queryset = (
            Order.objects
            .select_related('user', 'courier')
            .prefetch_related('items')
            .order_by('-created_at')
        )

        search_query = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        is_paid = self.request.GET.get('is_paid', '').strip()
        delivery_method = self.request.GET.get('delivery_method', '').strip()

        if search_query:
            if search_query.isdigit():
                queryset = queryset.filter(
                    Q(id=int(search_query)) |
                    Q(phone_number__icontains=search_query)
                )
            else:
                queryset = queryset.filter(
                    Q(user__username__icontains=search_query) |
                    Q(user__email__icontains=search_query) |
                    Q(recipient_name__icontains=search_query) |
                    Q(phone_number__icontains=search_query) |
                    Q(address__icontains=search_query) |
                    Q(tracking_note__icontains=search_query)
                )

        if status:
            queryset = queryset.filter(status=status)

        if is_paid == 'yes':
            queryset = queryset.filter(is_paid=True)
        elif is_paid == 'no':
            queryset = queryset.filter(is_paid=False)

        if delivery_method:
            queryset = queryset.filter(delivery_method=delivery_method)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['delivery_choices'] = Order.DELIVERY_CHOICES
        context['current_q'] = self.request.GET.get('q', '').strip()
        context['current_status'] = self.request.GET.get('status', '').strip()
        context['current_is_paid'] = self.request.GET.get('is_paid', '').strip()
        context['current_delivery_method'] = self.request.GET.get('delivery_method', '').strip()
        return context


class DashboardOrderDetailView(DashboardAccessMixin, DetailView):
    model = Order
    template_name = 'dashboard/orders/order_detail.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return (
            Order.objects
            .select_related('user', 'courier')
            .prefetch_related('items__product', 'status_history__changed_by')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_form'] = DashboardOrderStatusForm(initial={'status': self.object.status})
        return context


class DashboardOrderStatusUpdateView(DashboardAccessMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        form = DashboardOrderStatusForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Форма изменения статуса заполнена некорректно.")
            return redirect('dashboard:order_detail', order_id=order.id)

        new_status = form.cleaned_data['status']
        note = form.cleaned_data['note']

        try:
            order.set_status(new_status, note=note, changed_by=request.user)
            messages.success(request, f'Статус заказа #{order.id} изменён.')
        except Exception as exc:
            messages.error(request, f'Не удалось изменить статус заказа: {exc}')

        return redirect('dashboard:order_detail', order_id=order.id)


class DashboardProductListView(DashboardAccessMixin, ListView):
    model = Product
    template_name = 'dashboard/products/product_list.html'
    context_object_name = 'products'
    paginate_by = 15

    def get_queryset(self):
        queryset = (
            Product.objects
            .select_related('category', 'brand')
            .prefetch_related('sales')
            .order_by('-created_at')
        )

        self.filter_form = DashboardProductFilterForm(self.request.GET or None)

        if self.filter_form.is_valid():
            q = self.filter_form.cleaned_data.get('q')
            category = self.filter_form.cleaned_data.get('category')
            brand = self.filter_form.cleaned_data.get('brand')
            stock_state = self.filter_form.cleaned_data.get('stock_state')

            if q:
                queryset = queryset.filter(
                    Q(name__icontains=q) |
                    Q(slug__icontains=q) |
                    Q(description__icontains=q) |
                    Q(additional_info__icontains=q)
                )

            if category:
                queryset = queryset.filter(category=category)

            if brand:
                queryset = queryset.filter(brand=brand)

            if stock_state == 'in_stock':
                queryset = queryset.filter(stock__gt=5)
            elif stock_state == 'low_stock':
                queryset = queryset.filter(stock__gt=0, stock__lte=5)
            elif stock_state == 'out_of_stock':
                queryset = queryset.filter(stock=0)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        return context


class DashboardProductCreateView(DashboardAccessMixin, CreateView):
    model = Product
    form_class = DashboardProductForm
    template_name = 'dashboard/products/product_form.html'
    success_url = reverse_lazy('dashboard:product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Товар успешно создан.')
        return super().form_valid(form)


class DashboardProductUpdateView(DashboardAccessMixin, UpdateView):
    model = Product
    form_class = DashboardProductForm
    template_name = 'dashboard/products/product_form.html'
    context_object_name = 'product'
    pk_url_kwarg = 'product_id'
    success_url = reverse_lazy('dashboard:product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Товар успешно обновлён.')
        return super().form_valid(form)


class DashboardProductDeleteView(DashboardAccessMixin, DeleteView):
    model = Product
    template_name = 'dashboard/products/product_confirm_delete.html'
    context_object_name = 'product'
    pk_url_kwarg = 'product_id'
    success_url = reverse_lazy('dashboard:product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Товар успешно удалён.')
        return super().form_valid(form)