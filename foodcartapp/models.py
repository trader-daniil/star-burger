from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import Sum, F
from functools import reduce
from coordinates import find_coordinates
import geopy.distance


class Restaurant(models.Model):
    name = models.CharField(
        verbose_name='название',
        max_length=64,
    )
    address = models.CharField(
        verbose_name='адрес',
        max_length=128,
        blank=True,
    )
    contact_phone = PhoneNumberField(
        verbose_name='Нормализированный номер телефона',
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        verbose_name='название категории',
        max_length=64,
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        verbose_name='название продукта',
        max_length=64,
        db_index=True,
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        verbose_name='цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(verbose_name='картинка')
    special_status = models.BooleanField(
        verbose_name='спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        verbose_name='описание',
        max_length=256,
        blank=True,
    )
    orders = models.ManyToManyField(
        'Order',
        through='OrderProduct',
    )
    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItemQuerySet(models.QuerySet):
    def get_restaurants_with_products(self):
        return self.annotate(restaurant_name=F('restaurant__name')) \
                   .annotate(product_name=F('product__name')) \
                   .annotate(restaurant_address=F('restaurant__address'))


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name='ресторан',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True,
    )
    objects = RestaurantMenuItemQuerySet.as_manager()

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f'{self.restaurant.name} - {self.product.name}'


class OrderQuerySet(models.QuerySet):

    def get_total_price(self):
        """Возвращает полную стоимость заказа."""
        orders_with_total_price = self.prefetch_related('order_detail') \
            .annotate(
                final_price=Sum(F('order_detail__amount') * F('order_detail__product_price')),
            )
        return orders_with_total_price

    def get_not_complete_orders(self):
        """Возвращаем все заказы, у которых статус меньше 4."""
        return self.filter(status__lt=4)
    
    def get_cooking_restaurant_name(self):
        """Добавляем поле с названием готовящего ресторана."""
        return self.annotate(restaurant_name=F('cooking_restaurant__name'))



class Order(models.Model):
    """Модель заказа."""
    ORDER_STATUSES = (
        (1, 'Необработанный заказ'),
        (2, 'Сборка'),
        (3, 'Доставляется'),
        (4, 'Выполнен')
    )
    PAYMENT_METHOD = (
        (1, 'Наличностью'),
        (2, 'Электронно')
    )
    firstname = models.CharField(
        verbose_name='Имя покупателя',
        max_length=128,
    )
    lastname = models.CharField(
        verbose_name='Фамилия покупателя',
        max_length=128,
        blank=True,
    )
    contact_phone = PhoneNumberField(
        verbose_name='Нормализированный номер телефона',
    )
    address = models.CharField(
        verbose_name='адрес',
        max_length=128,
    )
    total_price = models.DecimalField(
        verbose_name='Конечная стоимость заказа',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
    )
    products = models.ManyToManyField(
        Product,
        through='OrderProduct',
    )
    status = models.PositiveSmallIntegerField(
        choices=ORDER_STATUSES,
        verbose_name='статус заказа',
        default=1,
        db_index=True,
    )
    comment = models.TextField(
        verbose_name='Комментарий к заказу',
        blank=True,
    )
    payment = models.PositiveSmallIntegerField(
        choices=PAYMENT_METHOD,
        default=2,
        verbose_name='Способ оплаты',
        db_index=True,
    )
    cooking_restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.SET_NULL,
        related_name='cooking_orders',
        verbose_name='Ресторан, готовящий заказ',
        null=True,
    )
    registrated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время регистрации заказа',
        db_index=True,
    )
    called_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата и время звонка менеджера',
        db_index=True,
    )
    delivered_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата и время доставки',
        db_index=True,
    )
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    @staticmethod
    def find_common_restaurant(restaurants):
        """Получаем список со списками ресторанов,
        возвращаем те, которые фигурируют во всех списках
        :param restaurants: список ресторанов для каждого продукта.
        """
        if not restaurants:
            return None
        suitable_rests = list(reduce(
            lambda i, j: i & j, (set(restaurant) for restaurant in restaurants)
        ))
        return suitable_rests
    
    def find_suitable_restaurants(
            self, restaurants_products,
            addresses, order_coordinates):
        """Для каждого продукта в заказе получаем список с ресторанами,
        способными приготовить этот продукт
        :param restaurants_products: Ресторан с продуктом, названием рестонана
        :param addresses: Все адреса в БД в формате словаря
        :param order_coordinates: Координаты адреса доставки.
        """
        suitable_restaurants = []
        for product in self.products.all():
            rests_for_product = []
            for restaurant_product in restaurants_products:
                if not restaurant_product.product_name == product.name:
                    continue
                restaurant_coordinates = find_coordinates(
                    address=restaurant_product.restaurant_address,
                    coordinates=addresses,
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
        return suitable_restaurants


class OrderProduct(models.Model):
    """Модель продукта в заказе."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Продукт',
        related_name='order_details',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество продуктов',
        validators=[MinValueValidator(1)],
    )
    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        on_delete=models.CASCADE,
        related_name='order_detail',
    )
    product_price = models.DecimalField(
        verbose_name='цена продукта',
        help_text='цена одного продукта на момент оформления заказа',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
