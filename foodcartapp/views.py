from django.http import JsonResponse
from django.templatetags.static import static
import json
from django.shortcuts import render

from .models import Product, Order, OrderProduct
from rest_framework.generics import CreateAPIView, UpdateAPIView, DestroyAPIView
from .serializers import OrderSerializer
from django.db import transaction


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def test_template(request):
    return render(
        request=request,
        template_name='test.html',
    )



def register_order(request):
    """Создание заказа из запроса."""
    response = json.loads(request.body)
    order = Order.objects.create(
        firstname=response['firstname'],
        lastname=response['lastname'],
        contact_phone=response['phonenumber'],
        address=response['address'],
    )
    for product in response['products']:
        sended_product = Product.objects.get(id=product['product'])
        OrderProduct.objects.create(
            product=sended_product,
            order=order,
            amount=product['quantity']

        )
    return JsonResponse({})

"""
def check_products(order_datail):
    Проверка правильно переданных продуктов
    if not order_datail.get('products', '') or not isinstance(order_datail.get('products', ''), list):
        raise ValueError()
"""


class OrderCreateView(CreateAPIView):
    """Создает заказ."""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderUpdateDeleteView(UpdateAPIView, DestroyAPIView):
    """Получает и удаляет заказ."""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_field='pk'
    
    def get_serializer_context(self):
        context = super(OrderUpdateDeleteView, self).get_serializer_context()
        context.update({'request': self.request})
        return context
