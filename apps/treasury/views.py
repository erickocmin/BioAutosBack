from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import HasModulePermission
from common.services import audit
from common.viewsets import AuditedModelViewSet
from .models import Arqueo, Caja, CierreDiario, FormaPago
from .serializers import ArqueoDetalleSerializer, ArqueoSerializer, CajaSerializer, CierreDiarioSerializer, ConteoSerializer, FormaPagoSerializer
from .services import add_cash_count_detail, close_cash_count, replace_cash_count


class TreasuryViewSet(AuditedModelViewSet):
    permission_classes = [HasModulePermission]


class CajaViewSet(TreasuryViewSet):
    queryset = Caja.objects.select_related("sucursal", "sucursal__empresa").order_by("sucursal_id", "nombre")
    serializer_class = CajaSerializer
    permission_module = "treasury.cajas"
    scope_branch_lookup = "sucursal"
    filterset_fields = ["sucursal", "activa"]
    search_fields = ["codigo", "nombre"]


class FormaPagoViewSet(TreasuryViewSet):
    queryset = FormaPago.objects.order_by("nombre")
    serializer_class = FormaPagoSerializer
    permission_module = "treasury.formas_pago"


class ArqueoViewSet(TreasuryViewSet):
    queryset = Arqueo.objects.select_related("sucursal", "caja", "cajero", "cerrado_por").prefetch_related("detalles", "detalles__forma_pago", "conteos").order_by("-fecha", "-id")
    serializer_class = ArqueoSerializer
    permission_module = "treasury.arqueos"
    scope_branch_lookup = "sucursal"
    filterset_fields = ["sucursal", "caja", "cajero", "fecha", "estado"]
    ordering_fields = ["fecha", "created_at"]

    @action(detail=True, methods=["post"], url_path="detalles")
    def add_detail(self, request, pk=None):
        self.permission_action = "can_update"
        cash_count = self.get_object()
        serializer = ArqueoDetalleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        detail = add_cash_count_detail(cash_count=cash_count, data=serializer.validated_data)
        audit(actor=request.user, action="add_detail", instance=detail, request=request)
        return Response(ArqueoDetalleSerializer(detail).data, status=201)

    @action(detail=True, methods=["put"], url_path="conteo-efectivo")
    def cash_count(self, request, pk=None):
        self.permission_action = "can_update"
        serializer = ConteoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cash_count = self.get_object()
        total, difference = replace_cash_count(cash_count=cash_count, denominations=serializer.validated_data["denominaciones"])
        audit(actor=request.user, action="cash_count", instance=cash_count, request=request)
        return Response({"total_contado": total, "diferencia_vs_declarado": difference})

    @action(detail=True, methods=["post"], url_path="cerrar")
    def close(self, request, pk=None):
        self.permission_action = "can_close"
        cash_count = close_cash_count(cash_count=self.get_object(), user=request.user)
        audit(actor=request.user, action="close", instance=cash_count, request=request)
        return Response(self.get_serializer(cash_count).data)

    def perform_create(self, serializer):
        cashbox = serializer.validated_data["caja"]
        employee = getattr(self.request.user, "empleado", None)
        if employee and not self.request.user.is_superuser and employee.sucursal_id != cashbox.sucursal_id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("La caja no pertenece a la sucursal del usuario.")
        instance = serializer.save(sucursal=cashbox.sucursal, cajero=self.request.user)
        audit(actor=self.request.user, action="create", instance=instance, request=self.request)


class CierreDiarioViewSet(TreasuryViewSet):
    queryset = CierreDiario.objects.select_related("sucursal", "creado_por").prefetch_related("arqueos").order_by("-fecha", "-id")
    serializer_class = CierreDiarioSerializer
    permission_module = "treasury.cierres_diarios"
    scope_branch_lookup = "sucursal"
    filterset_fields = ["sucursal", "fecha", "anulado"]

    def perform_create(self, serializer):
        instance = serializer.save(creado_por=self.request.user)
        audit(actor=self.request.user, action="create", instance=instance, request=self.request)
