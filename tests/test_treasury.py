from datetime import date
from decimal import Decimal

import pytest
from common.exceptions import Conflict

from apps.treasury.models import Arqueo, ArqueoDetalle, Caja, FormaPago
from apps.treasury.services import add_cash_count_detail, close_cash_count, replace_cash_count


@pytest.fixture
def cash_count(user, branch):
    cashbox = Caja.objects.create(sucursal=branch, codigo="C1", nombre="Caja principal")
    return Arqueo.objects.create(sucursal=branch, caja=cashbox, cajero=user, fecha=date(2026, 9, 20))


@pytest.mark.django_db
def test_cash_count_difference_is_calculated_server_side(cash_count):
    cash_count.total_efectivo = Decimal("100")
    cash_count.save()
    total, difference = replace_cash_count(cash_count=cash_count, denominations=[{"denominacion": 20, "cantidad": 4}, {"denominacion": 10, "cantidad": 1}])
    assert total == Decimal("90")
    assert difference == Decimal("-10")


@pytest.mark.django_db
def test_close_recalculates_totals(user, cash_count):
    cash = FormaPago.objects.create(codigo="EFE", nombre="Efectivo", es_efectivo=True)
    card = FormaPago.objects.create(codigo="TAR", nombre="Tarjeta")
    ArqueoDetalle.objects.create(arqueo=cash_count, numero_linea=1, categoria="income", forma_pago=cash, importe=80)
    ArqueoDetalle.objects.create(arqueo=cash_count, numero_linea=2, categoria="income", forma_pago=card, importe=20)
    result = close_cash_count(cash_count=cash_count, user=user)
    assert result.total_arqueo == Decimal("100")
    assert result.total_efectivo == Decimal("80")
    assert result.estado == Arqueo.Estado.CERRADO


@pytest.mark.django_db
def test_closed_cash_count_is_immutable_for_count(user, cash_count):
    close_cash_count(cash_count=cash_count, user=user)
    with pytest.raises(Conflict):
        replace_cash_count(cash_count=cash_count, denominations=[])


@pytest.mark.django_db
def test_unique_cash_count_per_context(user, cash_count):
    from django.db import IntegrityError
    with pytest.raises(IntegrityError):
        Arqueo.objects.create(sucursal=cash_count.sucursal, caja=cash_count.caja, cajero=user, fecha=cash_count.fecha)


@pytest.mark.django_db
def test_repeated_close_returns_conflict(user, cash_count):
    close_cash_count(cash_count=cash_count, user=user)
    with pytest.raises(Conflict) as error:
        close_cash_count(cash_count=cash_count, user=user)
    assert error.value.get_codes() == "cash_count_closed"


@pytest.mark.django_db
def test_detail_line_is_server_generated_and_closed_count_is_immutable(user, cash_count):
    payment = FormaPago.objects.create(codigo="EFE", nombre="Efectivo", es_efectivo=True)
    first = add_cash_count_detail(cash_count=cash_count, data={"categoria": "income", "forma_pago": payment, "importe": 10})
    second = add_cash_count_detail(cash_count=cash_count, data={"categoria": "income", "forma_pago": payment, "importe": 20})
    assert (first.numero_linea, second.numero_linea) == (1, 2)
    close_cash_count(cash_count=cash_count, user=user)
    with pytest.raises(Conflict):
        add_cash_count_detail(cash_count=cash_count, data={"categoria": "income", "importe": 1})
