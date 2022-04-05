from rest_framework import serializers

from main.models import Preorder, Position, Order
from main.models.orders import TYPE_SELL, TYPE_BUY


class PreorderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preorder
        fields = (
            'id',
            'preorder_id',
            'order_date',
            'finished_at',
            'buyer',
            'location',
            'sum_rub',
            'sum_btc',
            'product',
            'product_name',
            'size',
            'status',
            'status_text',
            'is_garant',
            'garant_status',
            'positions'
        )


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = (
            'id',
            'r_id',
            'created_at',
            'closed_at',
            'preorder',
            'status',
            'sum_btc',
            'orders',
            'order_in',
            'btc_price_in',
            'order_out',
            'btc_price_out',
            'is_by_hand',
            'h_preorder_id',
            'preorder_sum_rub',
            'is_preorder_garant'
        )


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('__all__')


class PositionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('id', 'status', 'comment')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        order_in_instance = instance.orders.filter(type=TYPE_SELL).first()
        order_out_instance = instance.orders.filter(type=TYPE_BUY).first()
        if order_in_instance:
            representation['order_in_data'] = OrderSerializer(order_in_instance).data
        if order_out_instance:
            representation['order_out_data'] = OrderSerializer(order_out_instance).data
        if order_in_instance and order_out_instance:
            position_margin = order_in_instance.price - order_out_instance.price
            representation['analytics'] = {
                'position_margin': position_margin,
                'position_margin_str': f'{order_in_instance.price} - {order_out_instance.price} = {position_margin}',
            }

        preorder_instance = instance.preorder
        if preorder_instance:
            representation['preorder_data'] = PreorderSerializer(preorder_instance).data

        return representation

















