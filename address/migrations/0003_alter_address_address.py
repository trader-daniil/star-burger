# Generated by Django 3.2.15 on 2023-02-27 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0002_address_last_handle_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='address',
            field=models.TextField(unique=True, verbose_name='Адрес места'),
        ),
    ]