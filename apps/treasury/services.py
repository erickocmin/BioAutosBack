from decimal import Decimal

from django.db import transaction
from django.db.models import Max, Sum
from django.utils import timezone

from common.exceptions import Conflict
from .models import Arqueo, ArqueoDetalle, ConteoEfectivo


@transaction.atomic
def replace_cash_count(*, cash_count, denominations):
    cash_count = Arqueo.objects.select_for_update().get(pk=cash_count.pk)
    if cash_count.estado != Arqueo.Estado.ABIERTO:
        raise Conflict("Solo puede modificarse el conteo de un arqueo abierto.", code="cash_count_closed")
    cash_count.conteos.all().delete()
    ConteoEfectivo.objects.bulk_create([
        ConteoEfectivo(arqueo=cash_count, denominacion=item["denominacion"], cantidad=item["cantidad"])
        for item in denominations if int(item["cantidad"]) > 0
    ])
    total = sum(Decimal(str(item["denominacion"])) * int(item["cantidad"]) for item in denominations)
    return total, total - cash_count.total_efectivo


@transaction.atomic
def close_cash_count(*, cash_count, user):
    cash_count = Arqueo.objects.select_for_update().get(pk=cash_count.pk)
    if cash_count.estado != Arqueo.Estado.ABIERTO:
        raise Conflict("El arqueo ya no está abierto.", code="cash_count_closed")
    detail_total = cash_count.detalles.aggregate(value=Sum("importe"))["value"] or Decimal("0")
    cash_count.total_arqueo = detail_total
    cash_count.total_efectivo = cash_count.detalles.filter(forma_pago__es_efectivo=True).aggregate(value=Sum("importe"))["value"] or Decimal("0")
    cash_count.estado = Arqueo.Estado.CERRADO
    cash_count.cerrado_at = timezone.now()
    cash_count.cerrado_por = user
    cash_count.save(update_fields=["total_arqueo", "total_efectivo", "estado", "cerrado_at", "cerrado_por", "updated_at"])
    return cash_count


@transaction.atomic
def add_cash_count_detail(*, cash_count, data):
    cash_count = Arqueo.objects.select_for_update().get(pk=cash_count.pk)
    if cash_count.estado != Arqueo.Estado.ABIERTO:
        raise Conflict("Solo puede modificarse un arqueo abierto.", code="cash_count_closed")
    next_line = (cash_count.detalles.aggregate(value=Max("numero_linea"))["value"] or 0) + 1
    detail = ArqueoDetalle.objects.create(arqueo=cash_count, numero_linea=next_line, **data)
    cash_count.total_arqueo = cash_count.detalles.aggregate(value=Sum("importe"))["value"] or Decimal("0")
    cash_count.total_efectivo = cash_count.detalles.filter(forma_pago__es_efectivo=True).aggregate(value=Sum("importe"))["value"] or Decimal("0")
    cash_count.save(update_fields=["total_arqueo", "total_efectivo", "updated_at"])
    return detail
