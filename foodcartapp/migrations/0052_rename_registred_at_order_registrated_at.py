# Generated by Django 4.1.5 on 2023-01-30 09:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0051_order_called_at_order_delivered_at_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='registred_at',
            new_name='registrated_at',
        ),
    ]
