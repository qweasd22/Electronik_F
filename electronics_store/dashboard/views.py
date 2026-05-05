from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from news.models import News
from orders.models import Order, OrderItem, SaleEvent
from products.models import Product, Review, Sale
from .forms import (
    DashboardCourierCreateForm,
    DashboardNewsFilterForm,
    DashboardNewsForm,
    DashboardOrderCourierAssignForm,
    DashboardOrderStatusForm,
    DashboardProductFilterForm,
    DashboardProductForm,
    DashboardReviewFilterForm,
    DashboardSaleFilterForm,
    DashboardSaleForm,
    DashboardUserFilterForm,
    DashboardUserUpdateForm,
)
from .mixins import CourierAccessMixin, DashboardAccessMixin

User = get_user_model()

DELIVERY_SUM_EXPRESSION = Case(
    When(delivery_method='standard', then=Value(Decimal('200.00'))),
    When(delivery_method='express', then=Value(Decimal('500.00'))),
    default=Value(Decimal('0.00')),
    output_field=DecimalField(max_digits=12, decimal_places=2),
)


def _calc_orders_revenue(order_queryset):
    items_total = (
        OrderItem.objects.filter(order__in=order_queryset)
        .aggregate(
            total=Sum(
                F('quantity') * F('price_at_purchase'),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        .get('total')
        or Decimal('0.00')
    )

    delivery_total = (
        order_queryset.aggregate(total=Sum(DELIVERY_SUM_EXPRESSION)).get('total')
        or Decimal('0.00')
    )

    return items_total + delivery_total


def _build_courier_stats(courier):
    orders_qs = Order.objects.filter(courier=courier)
    delivered_qs = orders_qs.filter(status='delivered')
    in_progress_qs = orders_qs.filter(status__in=['processing', 'paid', 'shipped'])
    cancelled_qs = orders_qs.filter(status='cancelled')

    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_delivered_qs = delivered_qs.filter(delivered_at__gte=month_start)

    delivered_revenue = _calc_orders_revenue(delivered_qs)
    month_revenue = _calc_orders_revenue(month_delivered_qs)
    delivered_count = delivered_qs.count()

    average_check = Decimal('0.00')
    if delivered_count:
        average_check = delivered_revenue / delivered_count

    return {
        'assigned_orders': orders_qs.count(),
        'in_progress_orders': in_progress_qs.count(),
        'delivered_orders': delivered_count,
        'cancelled_orders': cancelled_qs.count(),
        'delivered_revenue': delivered_revenue,
        'month_revenue': month_revenue,
        'average_check': average_check.quantize(Decimal('0.01')),
    }


class DashboardHomeView(DashboardAccessMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_orders = Order.objects.count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        paid_orders = Order.objects.filter(is_paid=True).exclude(status='cancelled').count()
        cancelled_orders = Order.objects.filter(status='cancelled').count()

        total_users = User.objects.count()
        total_products = Product.objects.count()
        low_stock_products = Product.objects.filter(stock__lte=5).count()
        total_couriers = User.objects.filter(is_courier=True).count()
        pending_reviews = Review.objects.filter(is_approved=False).count()

        delivered_revenue = _calc_orders_revenue(Order.objects.filter(status='delivered'))
        expected_revenue = _calc_orders_revenue(
            Order.objects.filter(is_paid=True).exclude(status='cancelled')
        )
        cancelled_revenue = _calc_orders_revenue(Order.objects.filter(status='cancelled'))

        recent_orders = Order.objects.select_related('user', 'courier').order_by('-created_at')[:5]
        recent_users = User.objects.order_by('-date_joined')[:5]
        low_stock_items = Product.objects.filter(stock__lte=5).order_by('stock')[:5]
        recent_sales = SaleEvent.objects.select_related('user', 'product', 'order').order_by('-timestamp')[:5]

        context.update(
            {
                'total_orders': total_orders,
                'delivered_orders': delivered_orders,
                'paid_orders': paid_orders,
                'cancelled_orders': cancelled_orders,
                'total_users': total_users,
                'total_products': total_products,
                'low_stock_products': low_stock_products,
                'total_couriers': total_couriers,
                'pending_reviews': pending_reviews,
                'delivered_revenue': delivered_revenue,
                'expected_revenue': expected_revenue,
                'cancelled_revenue': cancelled_revenue,
                'recent_orders': recent_orders,
                'recent_users': recent_users,
                'low_stock_items': low_stock_items,
                'recent_sales': recent_sales,
            }
        )
        return context


class DashboardOrderListView(DashboardAccessMixin, ListView):
    model = Order
    template_name = 'dashboard/orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 15

    def get_queryset(self):
        queryset = (
            Order.objects.select_related('user', 'courier').prefetch_related('items').order_by('-created_at')
        )

        search_query = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        is_paid = self.request.GET.get('is_paid', '').strip()
        delivery_method = self.request.GET.get('delivery_method', '').strip()
        courier_id = self.request.GET.get('courier', '').strip()

        if search_query:
            if search_query.isdigit():
                queryset = queryset.filter(Q(id=int(search_query)) | Q(phone_number__icontains=search_query))
            else:
                queryset = queryset.filter(
                    Q(user__username__icontains=search_query)
                    | Q(user__email__icontains=search_query)
                    | Q(recipient_name__icontains=search_query)
                    | Q(phone_number__icontains=search_query)
                    | Q(address__icontains=search_query)
                    | Q(tracking_note__icontains=search_query)
                )

        if status:
            queryset = queryset.filter(status=status)

        if is_paid == 'yes':
            queryset = queryset.filter(is_paid=True)
        elif is_paid == 'no':
            queryset = queryset.filter(is_paid=False)

        if delivery_method:
            queryset = queryset.filter(delivery_method=delivery_method)

        if courier_id:
            if courier_id == 'none':
                queryset = queryset.filter(courier__isnull=True)
            elif courier_id.isdigit():
                queryset = queryset.filter(courier_id=int(courier_id))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['delivery_choices'] = Order.DELIVERY_CHOICES
        context['couriers'] = User.objects.filter(is_active=True, is_courier=True).order_by('username')
        context['current_q'] = self.request.GET.get('q', '').strip()
        context['current_status'] = self.request.GET.get('status', '').strip()
        context['current_is_paid'] = self.request.GET.get('is_paid', '').strip()
        context['current_delivery_method'] = self.request.GET.get('delivery_method', '').strip()
        context['current_courier'] = self.request.GET.get('courier', '').strip()
        return context


class DashboardOrderDetailView(DashboardAccessMixin, DetailView):
    model = Order
    template_name = 'dashboard/orders/order_detail.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return (
            Order.objects.select_related('user', 'courier').prefetch_related('items__product', 'status_history__changed_by')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_form'] = DashboardOrderStatusForm(initial={'status': self.object.status})
        context['courier_form'] = DashboardOrderCourierAssignForm(initial={'courier': self.object.courier})

        couriers = User.objects.filter(is_active=True, is_courier=True).order_by('username')
        context['courier_stats_rows'] = [
            {'courier': courier, **_build_courier_stats(courier)} for courier in couriers
        ]
        return context


class DashboardOrderStatusUpdateView(DashboardAccessMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        form = DashboardOrderStatusForm(request.POST)

        if not form.is_valid():
            messages.error(request, 'Форма изменения статуса заполнена некорректно.')
            return redirect('dashboard:order_detail', order_id=order.id)

        new_status = form.cleaned_data['status']
        note = form.cleaned_data['note']

        try:
            order.set_status(new_status, note=note, changed_by=request.user)
            messages.success(request, f'Статус заказа #{order.id} изменён.')
        except Exception as exc:
            messages.error(request, f'Не удалось изменить статус заказа: {exc}')

        return redirect('dashboard:order_detail', order_id=order.id)


class DashboardOrderAssignCourierView(DashboardAccessMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        form = DashboardOrderCourierAssignForm(request.POST)

        if not form.is_valid():
            messages.error(request, 'Не удалось назначить курьера: проверьте данные формы.')
            return redirect('dashboard:order_detail', order_id=order.id)

        courier = form.cleaned_data['courier']
        order.courier = courier
        order.save(update_fields=['courier', 'updated_at'])

        if courier is None:
            messages.success(request, f'Курьер для заказа #{order.id} снят.')
        else:
            messages.success(request, f'Заказ #{order.id} назначен курьеру {courier.username}.')

        return redirect('dashboard:order_detail', order_id=order.id)


class DashboardProductListView(DashboardAccessMixin, ListView):
    model = Product
    template_name = 'dashboard/products/product_list.html'
    context_object_name = 'products'
    paginate_by = 15

    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'brand').prefetch_related('sales').order_by('-created_at')

        self.filter_form = DashboardProductFilterForm(self.request.GET or None)

        if self.filter_form.is_valid():
            q = self.filter_form.cleaned_data.get('q')
            category = self.filter_form.cleaned_data.get('category')
            brand = self.filter_form.cleaned_data.get('brand')
            stock_state = self.filter_form.cleaned_data.get('stock_state')

            if q:
                queryset = queryset.filter(
                    Q(name__icontains=q)
                    | Q(slug__icontains=q)
                    | Q(description__icontains=q)
                    | Q(additional_info__icontains=q)
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


class DashboardReviewListView(DashboardAccessMixin, ListView):
    model = Review
    template_name = 'dashboard/reviews/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 5

    def get_queryset(self):
        queryset = Review.objects.select_related('product', 'user').order_by('is_approved', '-created_at')

        self.filter_form = DashboardReviewFilterForm(self.request.GET or None)

        if self.filter_form.is_valid():
            q = self.filter_form.cleaned_data.get('q')
            product = self.filter_form.cleaned_data.get('product')
            is_approved = self.filter_form.cleaned_data.get('is_approved')

            if q:
                queryset = queryset.filter(
                    Q(product__name__icontains=q)
                    | Q(user__username__icontains=q)
                    | Q(user__email__icontains=q)
                    | Q(text__icontains=q)
                )

            if product:
                queryset = queryset.filter(product=product)

            if is_approved == 'yes':
                queryset = queryset.filter(is_approved=True)
            elif is_approved == 'no':
                queryset = queryset.filter(is_approved=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop('page', None)

        context['filter_form'] = self.filter_form
        context['pagination_query'] = query_params.urlencode()
        context['pending_reviews_count'] = Review.objects.filter(is_approved=False).count()
        context['approved_reviews_count'] = Review.objects.filter(is_approved=True).count()
        return context


class DashboardReviewStatusUpdateView(DashboardAccessMixin, View):
    def post(self, request, review_id):
        review = get_object_or_404(Review.objects.select_related('product'), id=review_id)
        action = request.POST.get('action')

        if action == 'approve':
            review.is_approved = True
            message = f'Отзыв к товару "{review.product.name}" одобрен.'
        elif action == 'unapprove':
            review.is_approved = False
            message = f'Отзыв к товару "{review.product.name}" снят с публикации.'
        else:
            messages.error(request, 'Неизвестное действие для отзыва.')
            return redirect('dashboard:review_list')

        review.save(update_fields=['is_approved'])
        messages.success(request, message)

        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)

        return redirect('dashboard:review_list')


class DashboardUserListView(DashboardAccessMixin, ListView):
    model = User
    template_name = 'dashboard/users/user_list.html'
    context_object_name = 'users'
    paginate_by = 15

    def get_queryset(self):
        queryset = User.objects.annotate(order_count=Count('orders')).order_by('-date_joined')

        self.filter_form = DashboardUserFilterForm(self.request.GET or None)

        if self.filter_form.is_valid():
            q = self.filter_form.cleaned_data.get('q')
            is_active = self.filter_form.cleaned_data.get('is_active')
            is_staff = self.filter_form.cleaned_data.get('is_staff')
            is_superuser = self.filter_form.cleaned_data.get('is_superuser')
            is_courier = self.filter_form.cleaned_data.get('is_courier')

            if q:
                queryset = queryset.filter(
                    Q(username__icontains=q)
                    | Q(email__icontains=q)
                    | Q(first_name__icontains=q)
                    | Q(last_name__icontains=q)
                    | Q(phone_number__icontains=q)
                )

            if is_active == 'yes':
                queryset = queryset.filter(is_active=True)
            elif is_active == 'no':
                queryset = queryset.filter(is_active=False)

            if is_staff == 'yes':
                queryset = queryset.filter(is_staff=True)
            elif is_staff == 'no':
                queryset = queryset.filter(is_staff=False)

            if is_superuser == 'yes':
                queryset = queryset.filter(is_superuser=True)
            elif is_superuser == 'no':
                queryset = queryset.filter(is_superuser=False)

            if is_courier == 'yes':
                queryset = queryset.filter(is_courier=True)
            elif is_courier == 'no':
                queryset = queryset.filter(is_courier=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        return context


class DashboardUserDetailView(DashboardAccessMixin, DetailView):
    model = User
    template_name = 'dashboard/users/user_detail.html'
    context_object_name = 'profile_user'
    pk_url_kwarg = 'user_id'

    def get_queryset(self):
        return User.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.object

        user_orders = (
            Order.objects.filter(user=profile_user)
            .select_related('courier')
            .prefetch_related('items__product')
            .order_by('-created_at')
        )

        context['user_form'] = DashboardUserUpdateForm(instance=profile_user)
        context['user_orders'] = user_orders
        context['user_stats'] = {
            'total_orders': user_orders.count(),
            'delivered_orders': user_orders.filter(status='delivered').count(),
            'cancelled_orders': user_orders.filter(status='cancelled').count(),
            'current_orders': user_orders.filter(status__in=['processing', 'paid', 'shipped']).count(),
        }

        if profile_user.is_courier:
            context['courier_stats'] = _build_courier_stats(profile_user)
            context['courier_assigned_orders'] = (
                Order.objects.filter(courier=profile_user)
                .select_related('user')
                .prefetch_related('items__product')
                .order_by('-created_at')[:15]
            )

        return context


class DashboardUserUpdateView(DashboardAccessMixin, UpdateView):
    model = User
    form_class = DashboardUserUpdateForm
    template_name = 'dashboard/users/user_form.html'
    context_object_name = 'profile_user'
    pk_url_kwarg = 'user_id'

    def get_success_url(self):
        return reverse_lazy('dashboard:user_detail', kwargs={'user_id': self.object.id})

    def form_valid(self, form):
        messages.success(self.request, 'Данные пользователя обновлены.')
        return super().form_valid(form)


class DashboardCourierListView(DashboardAccessMixin, ListView):
    model = User
    template_name = 'dashboard/couriers/courier_list.html'
    context_object_name = 'couriers'

    def get_queryset(self):
        return User.objects.filter(is_courier=True).order_by('username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courier_rows'] = [
            {'courier': courier, **_build_courier_stats(courier)}
            for courier in context['couriers']
        ]
        return context


class DashboardCourierCreateView(DashboardAccessMixin, FormView):
    template_name = 'dashboard/couriers/courier_form.html'
    form_class = DashboardCourierCreateForm
    success_url = reverse_lazy('dashboard:courier_list')

    def form_valid(self, form):
        courier = form.save()
        messages.success(self.request, f'Курьер {courier.username} успешно создан.')
        return super().form_valid(form)


class DashboardNewsListView(DashboardAccessMixin, ListView):
    model = News
    template_name = 'dashboard/news/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 15

    def get_queryset(self):
        queryset = News.objects.select_related('category').order_by('-published_at', '-id')

        self.filter_form = DashboardNewsFilterForm(self.request.GET or None)

        if self.filter_form.is_valid():
            q = self.filter_form.cleaned_data.get('q')
            category = self.filter_form.cleaned_data.get('category')
            is_published = self.filter_form.cleaned_data.get('is_published')

            if q:
                queryset = queryset.filter(
                    Q(title__icontains=q) | Q(summary__icontains=q) | Q(content__icontains=q)
                )

            if category:
                queryset = queryset.filter(category=category)

            if is_published == 'yes':
                queryset = queryset.filter(is_published=True)
            elif is_published == 'no':
                queryset = queryset.filter(is_published=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        return context


class DashboardNewsCreateView(DashboardAccessMixin, CreateView):
    model = News
    form_class = DashboardNewsForm
    template_name = 'dashboard/news/news_form.html'
    success_url = reverse_lazy('dashboard:news_list')

    def form_valid(self, form):
        messages.success(self.request, 'Новость успешно создана.')
        return super().form_valid(form)


class DashboardNewsUpdateView(DashboardAccessMixin, UpdateView):
    model = News
    form_class = DashboardNewsForm
    template_name = 'dashboard/news/news_form.html'
    context_object_name = 'news_item'
    pk_url_kwarg = 'news_id'
    success_url = reverse_lazy('dashboard:news_list')

    def form_valid(self, form):
        messages.success(self.request, 'Новость успешно обновлена.')
        return super().form_valid(form)


class DashboardNewsDeleteView(DashboardAccessMixin, DeleteView):
    model = News
    template_name = 'dashboard/news/news_confirm_delete.html'
    context_object_name = 'news_item'
    pk_url_kwarg = 'news_id'
    success_url = reverse_lazy('dashboard:news_list')

    def form_valid(self, form):
        messages.success(self.request, 'Новость успешно удалена.')
        return super().form_valid(form)


class DashboardNewsTogglePublishView(DashboardAccessMixin, View):
    def post(self, request, news_id):
        news_item = get_object_or_404(News, id=news_id)
        news_item.is_published = not news_item.is_published
        news_item.save(update_fields=['is_published'])

        if news_item.is_published:
            messages.success(request, f'Новость «{news_item.title}» опубликована.')
        else:
            messages.success(request, f'Новость «{news_item.title}» снята с публикации.')

        return redirect('dashboard:news_list')


class DashboardSaleListView(DashboardAccessMixin, ListView):
    model = Sale
    template_name = 'dashboard/sales/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 15

    def get_queryset(self):
        queryset = Sale.objects.prefetch_related('products').order_by('-start_date', '-id')

        self.filter_form = DashboardSaleFilterForm(self.request.GET or None)

        if self.filter_form.is_valid():
            q = self.filter_form.cleaned_data.get('q')
            is_active = self.filter_form.cleaned_data.get('is_active')
            current_state = self.filter_form.cleaned_data.get('current_state')
            now = timezone.now()

            if q:
                queryset = queryset.filter(name__icontains=q)

            if is_active == 'yes':
                queryset = queryset.filter(is_active=True)
            elif is_active == 'no':
                queryset = queryset.filter(is_active=False)

            if current_state == 'current':
                queryset = queryset.filter(is_active=True, start_date__lte=now).filter(
                    Q(end_date__isnull=True) | Q(end_date__gte=now)
                )
            elif current_state == 'upcoming':
                queryset = queryset.filter(start_date__gt=now)
            elif current_state == 'expired':
                queryset = queryset.filter(end_date__isnull=False, end_date__lt=now)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        context['now'] = timezone.now()
        return context


class DashboardSaleCreateView(DashboardAccessMixin, CreateView):
    model = Sale
    form_class = DashboardSaleForm
    template_name = 'dashboard/sales/sale_form.html'
    success_url = reverse_lazy('dashboard:sale_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Скидка успешно создана.')
        return response


class DashboardSaleUpdateView(DashboardAccessMixin, UpdateView):
    model = Sale
    form_class = DashboardSaleForm
    template_name = 'dashboard/sales/sale_form.html'
    context_object_name = 'sale'
    pk_url_kwarg = 'sale_id'
    success_url = reverse_lazy('dashboard:sale_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Скидка успешно обновлена.')
        return response


class DashboardSaleDeleteView(DashboardAccessMixin, DeleteView):
    model = Sale
    template_name = 'dashboard/sales/sale_confirm_delete.html'
    context_object_name = 'sale'
    pk_url_kwarg = 'sale_id'
    success_url = reverse_lazy('dashboard:sale_list')

    def form_valid(self, form):
        messages.success(self.request, 'Скидка успешно удалена.')
        return super().form_valid(form)


class DashboardSaleToggleActiveView(DashboardAccessMixin, View):
    def post(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)
        sale.is_active = not sale.is_active
        sale.save(update_fields=['is_active'])

        if sale.is_active:
            messages.success(request, f'Скидка «{sale.name}» активирована.')
        else:
            messages.success(request, f'Скидка «{sale.name}» деактивирована.')

        return redirect('dashboard:sale_list')


class CourierDashboardHomeView(CourierAccessMixin, TemplateView):
    template_name = 'dashboard/courier/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        courier_orders = (
            Order.objects.filter(courier=self.request.user)
            .select_related('user')
            .prefetch_related('items__product')
            .order_by('-created_at')
        )

        delivered_orders = courier_orders.filter(status='delivered')
        in_progress_orders = courier_orders.filter(status__in=['processing', 'paid', 'shipped'])

        context['stats'] = _build_courier_stats(self.request.user)
        context['recent_assigned_orders'] = in_progress_orders[:10]
        context['recent_delivered_orders'] = delivered_orders[:10]
        return context


class CourierOrderListView(CourierAccessMixin, ListView):
    model = Order
    template_name = 'dashboard/courier/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            Order.objects.filter(courier=self.request.user)
            .select_related('user')
            .prefetch_related('items__product')
            .order_by('-created_at')
        )

        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '').strip()
        return context


class CourierOrderDetailView(CourierAccessMixin, DetailView):
    model = Order
    template_name = 'dashboard/courier/order_detail.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return (
            Order.objects.filter(courier=self.request.user)
            .select_related('user', 'courier')
            .prefetch_related('items__product', 'status_history__changed_by')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status_form = DashboardOrderStatusForm(initial={'status': self.object.status})
        status_form.fields['note'].widget.attrs['placeholder'] = 'Комментарий к смене статуса'
        context['status_form'] = status_form
        return context


class CourierOrderStatusUpdateView(CourierAccessMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, courier=request.user)
        form = DashboardOrderStatusForm(request.POST)

        if not form.is_valid():
            messages.error(request, 'Проверьте данные формы изменения статуса.')
            return redirect('courier_dashboard:order_detail', order_id=order.id)

        new_status = form.cleaned_data['status']
        note = form.cleaned_data['note']

        try:
            order.set_status(new_status, note=note, changed_by=request.user)
            messages.success(request, f'Статус заказа #{order.id} обновлён.')
        except Exception as exc:
            messages.error(request, f'Не удалось обновить статус заказа: {exc}')

        return redirect('courier_dashboard:order_detail', order_id=order.id)
