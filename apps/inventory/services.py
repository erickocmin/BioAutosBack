from decimal import Decimal

from django.db import IntegrityError, transaction

from common.exceptions import Conflict
from .models import Kardex, MovimientoInventario, MovimientoInventarioDetalle, Producto, ProductoStock, UnidadMedida


def _locked_stock(product_id, warehouse_id):
    stock, _ = ProductoStock.objects.select_for_update().get_or_create(
        producto_id=product_id, almacen_id=warehouse_id, defaults={"cantidad": Decimal("0")}
    )
    return stock


def _base_quantity(quantity, unit):
    return Decimal(str(quantity)) * unit.factor_base


def _validate_warehouse_scope(branch, *warehouses):
    if any(warehouse.sucursal_id != branch.pk for warehouse in warehouses):
        raise Conflict("El almacén no pertenece a la sucursal indicada.", code="warehouse_branch_mismatch")


def _ensure_new_operation(operation_id):
    if operation_id and MovimientoInventario.objects.filter(idempotency_key=operation_id).exists():
        raise Conflict("Esta operación ya fue registrada.", code="duplicate_operation")


def _create_movement(**values):
    try:
        with transaction.atomic():
            return MovimientoInventario.objects.create(**values)
    except IntegrityError:
        if values.get("idempotency_key"):
            raise Conflict("Esta operación ya fue registrada.", code="duplicate_operation")
        raise


@transaction.atomic
def register_purchase(*, branch, warehouse, supplier, items, user, reference="", operation_id=None):
    _validate_warehouse_scope(branch, warehouse)
    _ensure_new_operation(operation_id)
    movement = _create_movement(
        tipo=MovimientoInventario.Tipo.COMPRA, sucursal=branch, almacen_destino=warehouse,
        proveedor=supplier, referencia=reference, creado_por=user,
        **({"idempotency_key": operation_id} if operation_id else {}),
    )
    for item in items:
        product = Producto.objects.get(pk=item["producto_id"], activo=True)
        unit = UnidadMedida.objects.get(pk=item["unidad_medida_id"], activa=True)
        amount = _base_quantity(item["cantidad"], unit)
        cost = Decimal(str(item.get("costo_unitario", 0)))
        stock = _locked_stock(product.pk, warehouse.pk)
        stock.cantidad += amount
        stock.ultimo_costo = cost
        stock.save(update_fields=["cantidad", "ultimo_costo", "updated_at"])
        MovimientoInventarioDetalle.objects.create(
            movimiento=movement, producto=product, unidad_medida=unit,
            cantidad=item["cantidad"], cantidad_base=amount, costo_unitario=cost,
        )
        Kardex.objects.create(
            movimiento=movement, producto=product, almacen=warehouse,
            direccion=Kardex.Direccion.ENTRADA, cantidad=amount, saldo=stock.cantidad, costo_unitario=cost,
        )
    return movement


@transaction.atomic
def register_output(*, branch, warehouse, items, user, reference="", observation="", operation_id=None):
    _validate_warehouse_scope(branch, warehouse)
    _ensure_new_operation(operation_id)
    movement = _create_movement(
        tipo=MovimientoInventario.Tipo.SALIDA, sucursal=branch, almacen_origen=warehouse,
        referencia=reference, observacion=observation, creado_por=user,
        **({"idempotency_key": operation_id} if operation_id else {}),
    )
    for item in items:
        product = Producto.objects.get(pk=item["producto_id"], activo=True)
        unit = UnidadMedida.objects.get(pk=item["unidad_medida_id"], activa=True)
        amount = _base_quantity(item["cantidad"], unit)
        stock = _locked_stock(product.pk, warehouse.pk)
        if stock.cantidad < amount:
            raise Conflict(f"Stock insuficiente para {product.nombre}.", code="insufficient_stock")
        stock.cantidad -= amount
        stock.save(update_fields=["cantidad", "updated_at"])
        MovimientoInventarioDetalle.objects.create(
            movimiento=movement, producto=product, unidad_medida=unit,
            cantidad=item["cantidad"], cantidad_base=amount, costo_unitario=stock.ultimo_costo,
        )
        Kardex.objects.create(
            movimiento=movement, producto=product, almacen=warehouse,
            direccion=Kardex.Direccion.SALIDA, cantidad=amount, saldo=stock.cantidad,
            costo_unitario=stock.ultimo_costo,
        )
    return movement


@transaction.atomic
def register_transfer(*, branch, origin, destination, items, user, reference="", operation_id=None):
    _validate_warehouse_scope(branch, origin, destination)
    _ensure_new_operation(operation_id)
    if origin.pk == destination.pk:
        raise Conflict("Los almacenes de origen y destino deben ser distintos.", code="same_warehouse")
    movement = _create_movement(
        tipo=MovimientoInventario.Tipo.TRASLADO, sucursal=branch,
        almacen_origen=origin, almacen_destino=destination, referencia=reference, creado_por=user,
        **({"idempotency_key": operation_id} if operation_id else {}),
    )
    for item in items:
        product = Producto.objects.get(pk=item["producto_id"], activo=True)
        unit = UnidadMedida.objects.get(pk=item["unidad_medida_id"], activa=True)
        amount = _base_quantity(item["cantidad"], unit)
        stocks = {stock.almacen_id: stock for stock in ProductoStock.objects.select_for_update().filter(
            producto=product, almacen_id__in=sorted([origin.pk, destination.pk]))}
        origin_stock = stocks.get(origin.pk) or _locked_stock(product.pk, origin.pk)
        destination_stock = stocks.get(destination.pk) or _locked_stock(product.pk, destination.pk)
        if origin_stock.cantidad < amount:
            raise Conflict(f"Stock insuficiente para {product.nombre}.", code="insufficient_stock")
        origin_stock.cantidad -= amount
        destination_stock.cantidad += amount
        origin_stock.save(update_fields=["cantidad", "updated_at"])
        destination_stock.save(update_fields=["cantidad", "updated_at"])
        MovimientoInventarioDetalle.objects.create(
            movimiento=movement, producto=product, unidad_medida=unit,
            cantidad=item["cantidad"], cantidad_base=amount, costo_unitario=origin_stock.ultimo_costo,
        )
        Kardex.objects.bulk_create([
            Kardex(movimiento=movement, producto=product, almacen=origin, direccion=Kardex.Direccion.SALIDA,
                   cantidad=amount, saldo=origin_stock.cantidad, costo_unitario=origin_stock.ultimo_costo),
            Kardex(movimiento=movement, producto=product, almacen=destination, direccion=Kardex.Direccion.ENTRADA,
                   cantidad=amount, saldo=destination_stock.cantidad, costo_unitario=origin_stock.ultimo_costo),
        ])
    return movement
