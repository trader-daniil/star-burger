# Generated by Django 4.1.5 on 2023-01-30 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0047_alter_order_total_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Необработанный заказ'), (2, 'Сборка'), (3, 'Доставляется'), (4, 'Выполнен')], default=1, verbose_name='статус заказа'),
        ),
    ]
