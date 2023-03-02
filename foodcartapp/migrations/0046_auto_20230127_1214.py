from django.db import migrations
from django.db.models import F, Sum

def count_total_price_order(apps, schema_editor):
    """Вычисляем общую стоимость заказа по текущим ценам."""
    Order = apps.get_model('foodcartapp', 'Order')
    orders = Order.objects.all().annotate(
        price_of_order=Sum(F('products_amount__product__price')*F('products_amount__amount')) 
    )
    for order in orders.iterator():
        if order.price_of_order is None:
            order.total_price = 0
            order.save(update_fields=['total_price'])
            continue
        order.total_price=order.price_of_order
        order.save(update_fields=['total_price'])

class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0045_alter_orderproduct_order'),
    ]

    operations = [
        migrations.RunPython(count_total_price_order),
    ]
