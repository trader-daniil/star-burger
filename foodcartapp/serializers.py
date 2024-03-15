from .models import Order, Product, OrderProduct
from rest_framework import serializers
from rest_framework.response import Response
from django.db import transaction

class OrderProductSerializer(serializers.ModelSerializer):
    """Сериализатор продукта для OrderProduct"""
    quantity = serializers.IntegerField(source='amount')
    class Meta:
        model = OrderProduct
        fields = (
            'product',
            'quantity', 
        )


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор заказа."""
    products = OrderProductSerializer(
        many=True,
        write_only=True,
    )
    phonenumber = serializers.CharField(source='contact_phone')

    class Meta:
        model = Order
        fields = (
            'id',
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'products',
        )

    def validate(self, data):
        if self.context['request'].method == 'POST' and not data['products']:
            raise serializers.ValidationError('Укажите продукты')
        return data

    @transaction.atomic
    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        order_products = [
            OrderProduct(
                order=order,
                product=product_data['product'],
                amount=product_data['amount'],
                product_price=product_data['product'].price,
            ) for product_data in products_data
        ]
        OrderProduct.objects.bulk_create(order_products)
        final_price = Order.objects.filter(id=order.id)\
                                   .get_total_price()\
                                   .first()\
                                   .final_price
        order.total_price = final_price
        order.save(update_fields=['total_price'])
        return order
