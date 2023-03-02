from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.db.models import F, Sum, Prefetch

from django.urls import reverse
from functools import reduce
from django.db.models import Prefetch
from coordinates import fetch_coordinates
from environs import Env
import geopy.distance


from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from address.models import Address


env = Env()
env.read_env()
YANDEX_GEOCODE_API_KEY = env('YANDEX_GEOCODE_API_KEY')
GEOCODE_URL = 'https://geocode-maps.yandex.ru/1.x'


def find_coordinates(address, coordinates):
    """
    Получаем широту и долготу адреса
    Если нет совпадений в БД, то обращаемся к Geocode Api
    :param address: адрес, который нужно найти
    :param coordinates: словарь с адресом и координатами 
    """
    try:
        return coordinates[address]
    except KeyError:
        return fetch_coordinates(
            address=address,
            yandex_token=YANDEX_GEOCODE_API_KEY,
        )


def find_common_restaurant(restaurants):
    """Получаем список со списками ресторанов,
    возвращаем те, которые фигурируют во всех списках.
    """
    if not restaurants:
        return None
    suitable_rests = list(reduce(lambda i, j: i & j, (set(x) for x in restaurants)))
    return suitable_rests


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [
            availability.get(restaurant.id, False) for restaurant in restaurants
        ]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.filter(status__lt=4) \
        .prefetch_related('products') \
        .annotate(restaurant_name=F('cooking_restaurant__name')) \
        .order_by('status')
    restaurants_products = RestaurantMenuItem.objects \
        .annotate(restaurant_name=F('restaurant__name')) \
        .annotate(product_name=F('product__name')) \
        .annotate(restaurant_address=F('restaurant__address'))

    #address_in_db = Address.objects.values('address', 'latitude', 'longitude')
    address_in_db = {
        address.address: (address.longitude, address.latitude) for address in Address.objects.all()
    }

    # Для каждого заказа найдем рестораны, способные приготовить все продукты
    for order in orders:
        if order.restaurant_name:
            continue
        order_coordinates = find_coordinates(
            address=order.address,
            coordinates=address_in_db,
        )
        suitable_restaurants = []
        for product in order.products.all():
            rests_for_product = []
            for restaurant_product in restaurants_products:
                if not restaurant_product.product_name == product.name:
                    continue
                restaurant_coordinates = find_coordinates(
                    address=restaurant_product.restaurant_address,
                    coordinates=address_in_db,
                )
                distance = geopy.distance.geodesic(
                    order_coordinates,
                    restaurant_coordinates,
                ).km
                rests_for_product.append(
                    f'{restaurant_product.restaurant_name} - {round(distance, 2)} км',
                )
                distance = geopy.distance.geodesic(
                    order_coordinates,
                    restaurant_coordinates,
                ).km
            suitable_restaurants.append(rests_for_product)
        order.suitable_restaurants = find_common_restaurant(
            restaurants=suitable_restaurants,
        )

    return render(
        request,
        template_name='order_items.html',
        context={'order_items': orders},
    )
