from decimal import Decimal
from uuid import uuid4

import pytest
from common.exceptions import Conflict

from apps.inventory.models import Almacen, Kardex, Marca, Producto, ProductoStock, Proveedor, UnidadMedida
from apps.inventory.services import register_output, register_purchase, register_transfer


@pytest.fixture
def inventory_data(branch):
    unit = UnidadMedida.objects.create(codigo="UND", nombre="Unidad", factor_base=1)
    brand = Marca.objects.create(nombre="Demo")
    product = Producto.objects.create(codigo="P001", nombre="Aceite", marca=brand, unidad_base=unit)
    origin = Almacen.objects.create(sucursal=branch, codigo="A1", nombre="Principal")
    destination = Almacen.objects.create(sucursal=branch, codigo="A2", nombre="Secundario")
    supplier = Proveedor.objects.create(ruc="20987654321", razon_social="Proveedor Demo")
    return unit, product, origin, destination, supplier


@pytest.mark.django_db
def test_purchase_reloads_and_increments_stock(user, branch, inventory_data):
    unit, product, origin, _, supplier = inventory_data
    ProductoStock.objects.create(producto=product, almacen=origin, cantidad=5)
    register_purchase(branch=branch, warehouse=origin, supplier=supplier, user=user, items=[{"producto_id": product.pk, "unidad_medida_id": unit.pk, "cantidad": 3, "costo_unitario": 7}])
    assert ProductoStock.objects.get(producto=product, almacen=origin).cantidad == Decimal("8")
    assert Kardex.objects.filter(direccion="in").count() == 1


@pytest.mark.django_db
def test_output_blocks_negative_stock(user, branch, inventory_data):
    unit, product, origin, _, _ = inventory_data
    ProductoStock.objects.create(producto=product, almacen=origin, cantidad=2)
    with pytest.raises(Conflict):
        register_output(branch=branch, warehouse=origin, user=user, items=[{"producto_id": product.pk, "unidad_medida_id": unit.pk, "cantidad": 3}])
    assert ProductoStock.objects.get(producto=product, almacen=origin).cantidad == Decimal("2")


@pytest.mark.django_db
def test_transfer_creates_both_kardex_entries(user, branch, inventory_data):
    unit, product, origin, destination, _ = inventory_data
    ProductoStock.objects.create(producto=product, almacen=origin, cantidad=10)
    register_transfer(branch=branch, origin=origin, destination=destination, user=user, items=[{"producto_id": product.pk, "unidad_medida_id": unit.pk, "cantidad": 4}])
    assert ProductoStock.objects.get(producto=product, almacen=origin).cantidad == Decimal("6")
    assert ProductoStock.objects.get(producto=product, almacen=destination).cantidad == Decimal("4")
    assert set(Kardex.objects.values_list("direccion", flat=True)) == {"in", "out"}


@pytest.mark.django_db
def test_unit_conversion_moves_base_units(user, branch, inventory_data):
    _, product, origin, _, supplier = inventory_data
    box = UnidadMedida.objects.create(codigo="CJ12", nombre="Caja x12", factor_base=12)
    register_purchase(branch=branch, warehouse=origin, supplier=supplier, user=user, items=[{"producto_id": product.pk, "unidad_medida_id": box.pk, "cantidad": 2, "costo_unitario": 10}])
    assert ProductoStock.objects.get(producto=product, almacen=origin).cantidad == Decimal("24")


@pytest.mark.django_db
def test_kardex_cannot_be_deleted(user, branch, inventory_data):
    unit, product, origin, _, supplier = inventory_data
    movement = register_purchase(branch=branch, warehouse=origin, supplier=supplier, user=user, items=[{"producto_id": product.pk, "unidad_medida_id": unit.pk, "cantidad": 1}])
    with pytest.raises(TypeError):
        movement.kardex_entries.get().delete()


@pytest.mark.django_db
def test_operation_id_prevents_double_purchase(user, branch, inventory_data):
    unit, product, origin, _, supplier = inventory_data
    operation_id = uuid4()
    payload = [{"producto_id": product.pk, "unidad_medida_id": unit.pk, "cantidad": 2, "costo_unitario": 3}]
    register_purchase(branch=branch, warehouse=origin, supplier=supplier, user=user, items=payload, operation_id=operation_id)
    with pytest.raises(Conflict) as error:
        register_purchase(branch=branch, warehouse=origin, supplier=supplier, user=user, items=payload, operation_id=operation_id)
    assert error.value.get_codes() == "duplicate_operation"
    assert ProductoStock.objects.get(producto=product, almacen=origin).cantidad == Decimal("2")


@pytest.mark.django_db
def test_transfer_rejects_same_warehouse(user, branch, inventory_data):
    unit, product, origin, _, _ = inventory_data
    with pytest.raises(Conflict) as error:
        register_transfer(branch=branch, origin=origin, destination=origin, user=user,
                          items=[{"producto_id": product.pk, "unidad_medida_id": unit.pk, "cantidad": 1}])
    assert error.value.get_codes() == "same_warehouse"
