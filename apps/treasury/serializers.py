from decimal import Decimal

from rest_framework import serializers

from .models import Arqueo, ArqueoDetalle, Caja, CierreDiario, ConteoEfectivo, FormaPago


class CajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caja
        fields = "__all__"


class FormaPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormaPago
        fields = "__all__"


class ArqueoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArqueoDetalle
        fields = "__all__"
        read_only_fields = ("arqueo", "numero_linea")


class ArqueoSerializer(serializers.ModelSerializer):
    detalles = ArqueoDetalleSerializer(many=True, read_only=True)
    total_contado = serializers.SerializerMethodField()
    diferencia = serializers.SerializerMethodField()

    class Meta:
        model = Arqueo
        fields = "__all__"
        read_only_fields = ("sucursal", "cajero", "total_arqueo", "total_efectivo", "estado", "cerrado_at", "cerrado_por")

    def get_total_contado(self, obj) -> Decimal:
        return sum(item.denominacion * item.cantidad for item in obj.conteos.all())

    def get_diferencia(self, obj) -> Decimal:
        return self.get_total_contado(obj) - obj.total_efectivo


class DenominacionSerializer(serializers.Serializer):
    denominacion = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    cantidad = serializers.IntegerField(min_value=0)


class ConteoSerializer(serializers.Serializer):
    denominaciones = DenominacionSerializer(many=True)


class CierreDiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CierreDiario
        fields = "__all__"
        read_only_fields = ("creado_por", "anulado")

    def validate(self, attrs):
        branch = attrs.get("sucursal", getattr(self.instance, "sucursal", None))
        cash_counts = attrs.get("arqueos", [])
        invalid = [item.pk for item in cash_counts if item.sucursal_id != branch.pk or item.estado != Arqueo.Estado.CERRADO]
        if invalid:
            raise serializers.ValidationError({"arqueos": "Todos los arqueos deben estar cerrados y pertenecer a la sucursal."})
        return attrs


class ConteoEfectivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConteoEfectivo
        fields = "__all__"
