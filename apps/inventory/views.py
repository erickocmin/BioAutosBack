from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from apps.core.models import Sucursal
from common.permissions import HasModulePermission
from common.services import audit
from common.viewsets import AuditedModelViewSet
from common.scoping import ScopedQuerysetMixin, require_branch_access
from .models import Almacen, Kardex, Marca, MovimientoInventario, Producto, Proveedor, UnidadMedida
from .serializers import (AlmacenSerializer, KardexSerializer, MarcaSerializer, MovimientoSerializer,
                          OutputSerializer, ProductoSerializer, ProveedorSerializer, PurchaseSerializer,
                          TransferSerializer, UnidadMedidaSerializer)
from .services import register_output, register_purchase, register_transfer


class InventoryModelViewSet(AuditedModelViewSet):
    permission_classes = [HasModulePermission]


class AlmacenViewSet(InventoryModelViewSet):
    queryset = Almacen.objects.select_related("sucursal", "sucursal__empresa").order_by("sucursal_id", "nombre")
    serializer_class = AlmacenSerializer
    permission_module = "inventory.almacenes"
    scope_branch_lookup = "sucursal"
    filterset_fields = ["sucursal", "activo"]
    search_fields = ["codigo", "nombre"]


class UnidadMedidaViewSet(InventoryModelViewSet):
    queryset = UnidadMedida.objects.order_by("nombre")
    serializer_class = UnidadMedidaSerializer
    permission_module = "inventory.unidades_medida"


class MarcaViewSet(InventoryModelViewSet):
    queryset = Marca.objects.order_by("nombre")
    serializer_class = MarcaSerializer
    permission_module = "inventory.marcas"


class ProveedorViewSet(InventoryModelViewSet):
    queryset = Proveedor.objects.order_by("razon_social")
    serializer_class = ProveedorSerializer
    permission_module = "inventory.proveedores"
    search_fields = ["ruc", "razon_social"]
    filterset_fields = ["activo"]


class ProductoViewSet(InventoryModelViewSet):
    queryset = Producto.objects.select_related("marca", "unidad_base").prefetch_related("stocks", "stocks__almacen").order_by("nombre", "id")
    serializer_class = ProductoSerializer
    permission_module = "inventory.productos"
    search_fields = ["codigo", "codigo_barras", "nombre"]
    filterset_fields = ["activo", "marca", "unidad_base"]
    ordering_fields = ["nombre", "codigo", "created_at"]


class KardexViewSet(ScopedQuerysetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Kardex.objects.select_related("producto", "almacen", "movimiento").order_by("-created_at", "-id")
    serializer_class = KardexSerializer
    permission_classes = [HasModulePermission]
    permission_module = "inventory.kardex"
    scope_branch_lookup = "almacen__sucursal"
    filterset_fields = ["producto", "almacen", "direccion", "movimiento__tipo"]
    ordering_fields = ["created_at"]


class MovementViewSet(ScopedQuerysetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = MovimientoInventario.objects.select_related("sucursal", "almacen_origen", "almacen_destino", "proveedor", "creado_por").prefetch_related("detalles").order_by("-created_at", "-id")
    serializer_class = MovimientoSerializer
    permission_classes = [HasModulePermission]
    permission_module = "inventory.movimientos"
    scope_branch_lookup = "sucursal"
    filterset_fields = ["tipo", "sucursal", "almacen_origen", "almacen_destino", "proveedor"]
    ordering_fields = ["created_at"]

    def get_serializer_class(self):
        kind = self.request.data.get("tipo") if self.action == "create" else None
        return {"purchase": PurchaseSerializer, "output": OutputSerializer, "transfer": TransferSerializer}.get(kind, MovimientoSerializer)

    def create(self, request, *args, **kwargs):
        kind = request.data.get("tipo")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        branch = get_object_or_404(Sucursal, pk=data["sucursal_id"])
        require_branch_access(request.user, branch.pk)
        if kind == "purchase":
            movement = register_purchase(branch=branch, warehouse=get_object_or_404(Almacen, pk=data["almacen_id"]),
                supplier=get_object_or_404(Proveedor, pk=data["proveedor_id"]), items=data["items"], user=request.user,
                reference=data.get("referencia", ""), operation_id=data["operation_id"])
        elif kind == "output":
            movement = register_output(branch=branch, warehouse=get_object_or_404(Almacen, pk=data["almacen_id"]),
                items=data["items"], user=request.user, reference=data.get("referencia", ""), observation=data.get("observacion", ""),
                operation_id=data["operation_id"])
        elif kind == "transfer":
            movement = register_transfer(branch=branch, origin=get_object_or_404(Almacen, pk=data["almacen_origen_id"]),
                destination=get_object_or_404(Almacen, pk=data["almacen_destino_id"]), items=data["items"], user=request.user,
                reference=data.get("referencia", ""), operation_id=data["operation_id"])
        else:
            return Response({"code": "invalid_type", "message": "Tipo de movimiento inválido."}, status=status.HTTP_400_BAD_REQUEST)
        audit(actor=request.user, action="create", instance=movement, request=request, context={"operation_id": str(data["operation_id"])})
        return Response(MovimientoSerializer(movement).data, status=status.HTTP_201_CREATED)
