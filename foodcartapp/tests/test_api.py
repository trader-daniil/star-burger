from rest_framework.test import APITestCase
from foodcartapp.models import Product, OrderProduct, Order
from rest_framework.test import APIClient
from django.urls import reverse


ALL_ORDERS_URL = reverse('foodcartapp:order-list')
STARTPAGE_URL = reverse('start_page')


class TestOrderApi(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.first_product = Product.objects.create(
            name='first burger',
            price=100.99,
        )
        self.second_product = Product.objects.create(
            name='second burger',
            price=49.99,
        )
        self.first_order = Order.objects.create(
            firstname='Dan',
            lastname='Lastname',
            contact_phone='+79991234567',
            address='Москва, Речной вокзал',
        )

    def test_getting_orders(self):
        """Получение всех заказов."""
        response = self.client.get(path=ALL_ORDERS_URL)
        self.assertEqual(response.json()[0]['id'], self.first_order.id)
        self.assertEqual(response.status_code, 200)

    def test_creating_order(self):
        """Создание заказа."""
        order_data = {
            'products': [
                {
                    'product': self.second_product.id,
                    'quantity': 2
                }
            ],
            'firstname': 'Ivan',
            'lastname': 'Ivanovich',
            'phonenumber': '+79991232311',
            'address': 'Москва, ул. Новый Арбат, 1',
        }
        self.client.post(
            path=ALL_ORDERS_URL,
            data=order_data,
            format='json',
        )
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(OrderProduct.objects.count(), 1)

    def test_create_order_without_products(self):
        """Создание закзаза не указав продукты."""
        order_data = {
            'firstname': 'Ivan',
            'lastname': 'Ivanovich',
            'contact_phone': '+79991232311',
            'address': 'Москва, ул. Новый Арбат, 1',
        }
        response = self.client.post(
            path=ALL_ORDERS_URL,
            data=order_data,
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 1)

