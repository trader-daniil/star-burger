# Generated by Django 4.1.5 on 2023-01-20 09:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0040_order_orderproduct_product_orders'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='first_name',
            new_name='firstname',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='last_name',
            new_name='lastname',
        ),
    ]
