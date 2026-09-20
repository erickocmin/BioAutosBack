from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Caja(TimeStampedModel):
    sucursal = models.ForeignKey("core.Sucursal", related_name="cajas", on_delete=models.PROTECT)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100)
    activa = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["sucursal", "codigo"], name="uq_caja_sucursal_codigo")]


class FormaPago(TimeStampedModel):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=80)
    es_efectivo = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)


class Arqueo(TimeStampedModel):
    class Estado(models.TextChoices):
        ABIERTO = "open", "Abierto"
        CERRADO = "closed", "Cerrado"
        ANULADO = "cancelled", "Anulado"

    sucursal = models.ForeignKey("core.Sucursal", related_name="arqueos", on_delete=models.PROTECT)
    caja = models.ForeignKey(Caja, related_name="arqueos", on_delete=models.PROTECT)
    cajero = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="arqueos", on_delete=models.PROTECT)
    fecha = models.DateField(db_index=True)
    total_arqueo = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_efectivo = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ABIERTO, db_index=True)
    cerrado_at = models.DateTimeField(null=True, blank=True)
    cerrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="arqueos_cerrados", null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["sucursal", "caja", "cajero", "fecha"], name="uq_arqueo_contexto_fecha")]
        indexes = [models.Index(fields=["sucursal", "fecha"]), models.Index(fields=["cajero", "fecha"])]


class ArqueoDetalle(models.Model):
    arqueo = models.ForeignKey(Arqueo, related_name="detalles", on_delete=models.PROTECT)
    numero_linea = models.PositiveIntegerField()
    categoria = models.CharField(max_length=40, db_index=True)
    forma_pago = models.ForeignKey(FormaPago, related_name="arqueo_detalles", null=True, blank=True, on_delete=models.PROTECT)
    descripcion = models.CharField(max_length=200, blank=True)
    importe = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["arqueo", "numero_linea"], name="uq_arqueo_numero_linea")]
        indexes = [models.Index(fields=["arqueo", "categoria"])]


class ConteoEfectivo(models.Model):
    arqueo = models.ForeignKey(Arqueo, related_name="conteos", on_delete=models.CASCADE)
    denominacion = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["arqueo", "denominacion"], name="uq_conteo_denominacion")]


class CierreDiario(TimeStampedModel):
    sucursal = models.ForeignKey("core.Sucursal", related_name="cierres_diarios", on_delete=models.PROTECT)
    fecha = models.DateField(db_index=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="cierres_diarios", on_delete=models.PROTECT)
    arqueos = models.ManyToManyField(Arqueo, related_name="cierres_diarios")
    numero_deposito = models.CharField(max_length=80, blank=True)
    importe_deposito = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    anulado = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["sucursal", "fecha"])]
