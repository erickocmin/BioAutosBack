from decimal import Decimal

from rest_framework import serializers

from .models import Almacen, Kardex, Marca, MovimientoInventario, Producto, ProductoStock, Proveedor, UnidadMedida


class AlmacenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Almacen
        fields = "__all__"


class UnidadMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadMedida
        fields = "__all__"


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = "__all__"


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = "__all__"


class ProductoStockSerializer(serializers.ModelSerializer):
    almacen_nombre = serializers.CharField(source="almacen.nombre", read_only=True)

    class Meta:
        model = ProductoStock
        fields = ("almacen", "almacen_nombre", "cantidad", "ultimo_costo")


class ProductoSerializer(serializers.ModelSerializer):
    stocks = ProductoStockSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = "__all__"


class KardexSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    almacen_nombre = serializers.CharField(source="almacen.nombre", read_only=True)

    class Meta:
        model = Kardex
        fields = "__all__"


class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoInventario
        fields = "__all__"


class MovementItemSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField(min_value=1)
    unidad_medida_id = serializers.IntegerField(min_value=1)
    cantidad = serializers.DecimalField(max_digits=14, decimal_places=4, min_value=Decimal("0.0001"))
    costo_unitario = serializers.DecimalField(max_digits=14, decimal_places=4, min_value=Decimal("0"), required=False)


class PurchaseSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField()
    sucursal_id = serializers.IntegerField(min_value=1)
    almacen_id = serializers.IntegerField(min_value=1)
    proveedor_id = serializers.IntegerField(min_value=1)
    referencia = serializers.CharField(max_length=100, required=False, allow_blank=True)
    items = MovementItemSerializer(many=True, allow_empty=False)


class OutputSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField()
    sucursal_id = serializers.IntegerField(min_value=1)
    almacen_id = serializers.IntegerField(min_value=1)
    referencia = serializers.CharField(max_length=100, required=False, allow_blank=True)
    observacion = serializers.CharField(required=False, allow_blank=True)
    items = MovementItemSerializer(many=True, allow_empty=False)


class TransferSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField()
    sucursal_id = serializers.IntegerField(min_value=1)
    almacen_origen_id = serializers.IntegerField(min_value=1)
    almacen_destino_id = serializers.IntegerField(min_value=1)
    referencia = serializers.CharField(max_length=100, required=False, allow_blank=True)
    items = MovementItemSerializer(many=True, allow_empty=False)
