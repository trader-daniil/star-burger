from django.contrib import admin
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from .models import (Product, ProductCategory,
    Restaurant, RestaurantMenuItem, Order)
from django.db.models import Sum, F


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass

class ProductInstance(admin.TabularInline):
    model = Product.orders.through

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ('registrated_at',)
    list_display = (
        'firstname',
        'lastname',
        'contact_phone',
        'address',
        'total_price',
        'status',
        'comment',
        'registrated_at',
        'called_at',
        'delivered_at',
        'payment',
    )
    inlines = (ProductInstance,)

    def response_change(self, request, obj):
        response = super(OrderAdmin, self).response_change(request, obj)
        next_url = request.GET.get('next', '')

        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts='http://127.0.0.1:8000/',
        ):
            return HttpResponseRedirect(next_url)
        else:
            return response

    def save_formset(self, request, form, formset, change):
        """Меняем финальную стоимость заказа при изменении состава заказа."""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()
        order = instances[0].order
        order_price = Order.objects.prefetch_related('order_detail')\
                                   .filter(id=order.id)\
                                   .aggregate(
            final_price=Sum(F('order_detail__amount') * F('order_detail__product_price')),
        )
        order.total_price = order_price['final_price']
        order.save(update_fields=['total_price'])
