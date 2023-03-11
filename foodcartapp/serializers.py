from .models import Order, Product, OrderProduct
from rest_framework import serializers
from rest_framework.response import Response


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

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        for product in products_data:
            OrderProduct.objects.create(
                order=order,
                product=product['product'],
                amount=product['amount'],
            )
        return order
