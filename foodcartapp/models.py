from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import Sum, F
from django.dispatch import receiver
from django.db.models.signals import pre_delete, pre_save
from django.core.exceptions import ObjectDoesNotExist


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
        orders_with_total_price = self.prefetch_related('products') \
                                      .prefetch_related('products_amount') \
                                      .annotate(
            price_of_order=Sum(
                F('products_amount__product__price')*F('products_amount__amount'),
            )
        )
        return orders_with_total_price


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


@receiver(pre_save, sender=Order)
def change_status_order(sender, instance, *args, **kwargs):
    """При указании ресторана, готовящего заказ, меняется статус на Сборка."""
    try:
        order_product_before_update = Order.objects.get(id=instance.id)
    except ObjectDoesNotExist:
        pass
    else:
        if not order_product_before_update.cooking_restaurant:
            instance.status = 2


@receiver(pre_save, sender=OrderProduct)
def correct_order_total_price(sender, instance, *args, **kwargs):
    """При уменьшении числа продуктов в заказе(amount)
    Уменьшается общая стоимость,
    при увеличении amount увеличивается total_price.
    """
    try:
        order_product_before_update = OrderProduct.objects.get(id=instance.id)
        order = order_product_before_update.order
    except ObjectDoesNotExist:
        order = instance.order
        order.total_price += instance.product.price * instance.amount
        order.save(update_fields=['total_price'])
    else:
        if order_product_before_update.amount > instance.amount:
            inequality = order_product_before_update.amount - instance.amount
            order.total_price -= inequality * instance.product.price
            order.save(update_fields=['total_price'])
        elif order_product_before_update.amount < instance.amount:
            inequality = instance.amount - order_product_before_update.amount
            order.total_price += inequality * instance.product.price
            order.save(update_fields=['total_price'])


@receiver(pre_delete, sender=OrderProduct)
def correct_total_price(sender, instance, *args, **kwargs):
    """После удаления продуктов из заказа,
    конечная стоимость пересчитывается."""
    order = instance.order
    order.total_price -= instance.amount * instance.product.price
    order.save(update_fields=['total_price'])
