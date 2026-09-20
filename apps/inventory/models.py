from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Almacen(TimeStampedModel):
    sucursal = models.ForeignKey("core.Sucursal", related_name="almacenes", on_delete=models.PROTECT)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=120)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["sucursal", "codigo"], name="uq_almacen_sucursal_codigo")]


class UnidadMedida(TimeStampedModel):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=80)
    factor_base = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    activa = models.BooleanField(default=True)


class Marca(TimeStampedModel):
    nombre = models.CharField(max_length=100, unique=True)
    activa = models.BooleanField(default=True)


class Proveedor(TimeStampedModel):
    ruc = models.CharField(max_length=11, unique=True)
    razon_social = models.CharField(max_length=200, db_index=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    activo = models.BooleanField(default=True, db_index=True)


class Producto(TimeStampedModel):
    codigo = models.CharField(max_length=40, unique=True)
    codigo_barras = models.CharField(max_length=80, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=180, db_index=True)
    marca = models.ForeignKey(Marca, related_name="productos", null=True, blank=True, on_delete=models.PROTECT)
    unidad_base = models.ForeignKey(UnidadMedida, related_name="productos", on_delete=models.PROTECT)
    stock_minimo = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    afecta_stock = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["activo", "nombre"])]


class ProductoStock(TimeStampedModel):
    producto = models.ForeignKey(Producto, related_name="stocks", on_delete=models.PROTECT)
    almacen = models.ForeignKey(Almacen, related_name="stocks", on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    ultimo_costo = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["producto", "almacen"], name="uq_stock_producto_almacen"),
            models.CheckConstraint(condition=models.Q(cantidad__gte=0), name="ck_stock_no_negativo"),
        ]
        indexes = [models.Index(fields=["almacen", "producto"])]


class MovimientoInventario(TimeStampedModel):
    class Tipo(models.TextChoices):
        COMPRA = "purchase", "Compra"
        SALIDA = "output", "Salida"
        TRASLADO = "transfer", "Traslado"
        AJUSTE = "adjustment", "Ajuste"

    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    sucursal = models.ForeignKey("core.Sucursal", related_name="movimientos_inventario", on_delete=models.PROTECT)
    almacen_origen = models.ForeignKey(Almacen, related_name="movimientos_salida", null=True, blank=True, on_delete=models.PROTECT)
    almacen_destino = models.ForeignKey(Almacen, related_name="movimientos_entrada", null=True, blank=True, on_delete=models.PROTECT)
    proveedor = models.ForeignKey(Proveedor, related_name="compras", null=True, blank=True, on_delete=models.PROTECT)
    referencia = models.CharField(max_length=100, blank=True, db_index=True)
    observacion = models.TextField(blank=True)
    idempotency_key = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="movimientos_inventario", on_delete=models.PROTECT)

    class Meta:
        indexes = [models.Index(fields=["sucursal", "created_at"]), models.Index(fields=["tipo", "created_at"])]


class MovimientoInventarioDetalle(models.Model):
    movimiento = models.ForeignKey(MovimientoInventario, related_name="detalles", on_delete=models.PROTECT)
    producto = models.ForeignKey(Producto, related_name="detalles_movimiento", on_delete=models.PROTECT)
    unidad_medida = models.ForeignKey(UnidadMedida, related_name="detalles_movimiento", on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=14, decimal_places=4)
    cantidad_base = models.DecimalField(max_digits=16, decimal_places=4)
    costo_unitario = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(cantidad__gt=0), name="ck_movdetalle_cantidad_positiva")]


class Kardex(models.Model):
    class Direccion(models.TextChoices):
        ENTRADA = "in", "Entrada"
        SALIDA = "out", "Salida"

    movimiento = models.ForeignKey(MovimientoInventario, related_name="kardex_entries", on_delete=models.PROTECT)
    producto = models.ForeignKey(Producto, related_name="kardex", on_delete=models.PROTECT)
    almacen = models.ForeignKey(Almacen, related_name="kardex", on_delete=models.PROTECT)
    direccion = models.CharField(max_length=3, choices=Direccion.choices)
    cantidad = models.DecimalField(max_digits=16, decimal_places=4)
    saldo = models.DecimalField(max_digits=16, decimal_places=4)
    costo_unitario = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["producto", "almacen", "-created_at"])]

    def delete(self, *args, **kwargs):
        raise TypeError("El kardex es inmutable.")
