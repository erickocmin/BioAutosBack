from rest_framework import serializers

from .models import Empresa, Oficina, SerieDocumento, Sucursal, TipoDocumento, Ubigeo


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = "__all__"


class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = "__all__"


class OficinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oficina
        fields = "__all__"


class UbigeoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubigeo
        fields = "__all__"


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = "__all__"


class SerieDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SerieDocumento
        fields = "__all__"
        read_only_fields = ("valor_siguiente",)
