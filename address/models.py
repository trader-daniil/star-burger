from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.dispatch import receiver
from django.db.models.signals import pre_save
from coordinates import fetch_coordinates
from django.conf import settings


class Address(models.Model):
    """Модель адреса."""
    address = models.TextField(
        verbose_name='Адрес места',
        unique=True,
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name='Широта',
        validators=[
            MaxValueValidator(90),
            MinValueValidator(-90),
        ]
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name='Долгота',
        validators=[
            MaxValueValidator(180),
            MinValueValidator(-180),
        ]
    )
    last_handle_date = models.DateField(
        auto_now=True,
        verbose_name='Дата крайнего обращения к Геокодеру',
    )

    class Meta:
        verbose_name = 'адрес'
        verbose_name_plural = 'адреса'


@receiver(pre_save, sender=Address)
def check_latitude_and_longitude(sender, instance, *args, **kwargs):
    if not (instance.latitude or instance.longitude):
        instance.longitude, instance.latitude = fetch_coordinates(
            instance.address,
            settings.YANDEX_GEOCODE_API_KEY,
        )
