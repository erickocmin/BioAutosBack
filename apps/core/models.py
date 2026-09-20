import re

from django.core.exceptions import ValidationError
from django.db import models, transaction

from common.models import TimeStampedModel


class Empresa(TimeStampedModel):
    ruc = models.CharField(max_length=11, unique=True)
    razon_social = models.CharField(max_length=200)
    nombre_comercial = models.CharField(max_length=150, blank=True)
    activa = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["razon_social"]

    def __str__(self):
        return self.razon_social


class Sucursal(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, related_name="sucursales", on_delete=models.PROTECT)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=250, blank=True)
    activa = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["empresa_id", "nombre"]
        constraints = [models.UniqueConstraint(fields=["empresa", "codigo"], name="uq_sucursal_empresa_codigo")]
        indexes = [models.Index(fields=["empresa", "activa"])]

    def __str__(self):
        return f"{self.empresa} - {self.nombre}"


class Oficina(TimeStampedModel):
    sucursal = models.ForeignKey(Sucursal, related_name="oficinas", on_delete=models.PROTECT)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=150)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["sucursal", "codigo"], name="uq_oficina_sucursal_codigo")]


class Ubigeo(models.Model):
    codigo_inei = models.CharField(max_length=6, primary_key=True)
    departamento = models.CharField(max_length=80, db_index=True)
    provincia = models.CharField(max_length=80, db_index=True)
    distrito = models.CharField(max_length=80, db_index=True)

    class Meta:
        ordering = ["departamento", "provincia", "distrito"]


class TipoDocumento(TimeStampedModel):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    codigo_sunat = models.CharField(max_length=4, blank=True, db_index=True)
    activo = models.BooleanField(default=True)


class Configuracion(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, related_name="configuraciones", on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursal, related_name="configuraciones", null=True, blank=True, on_delete=models.CASCADE)
    clave = models.CharField(max_length=100)
    scope_key = models.CharField(max_length=32, editable=False, default="global")
    valor = models.JSONField(default=dict)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["empresa", "scope_key", "clave"], name="uq_config_scope_clave")]

    def save(self, *args, **kwargs):
        self.scope_key = f"branch:{self.sucursal_id}" if self.sucursal_id else "global"
        super().save(*args, **kwargs)


class SerieDocumento(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, related_name="series_documento", on_delete=models.PROTECT)
    sucursal = models.ForeignKey(Sucursal, related_name="series_documento", on_delete=models.PROTECT)
    oficina = models.ForeignKey(Oficina, related_name="series_documento", null=True, blank=True, on_delete=models.PROTECT)
    tipo_documento = models.ForeignKey(TipoDocumento, related_name="series", on_delete=models.PROTECT)
    serie = models.CharField(max_length=10)
    valor_siguiente = models.PositiveBigIntegerField(default=1)
    valor_minimo = models.PositiveBigIntegerField(default=1)
    valor_maximo = models.PositiveBigIntegerField(default=99999999)
    incremento = models.PositiveIntegerField(default=1)
    activa = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["empresa", "tipo_documento", "serie"], name="uq_serie_empresa_tipo_serie"),
            models.CheckConstraint(condition=models.Q(valor_siguiente__gte=1), name="ck_serie_siguiente_positivo"),
            models.CheckConstraint(condition=models.Q(valor_maximo__gte=models.F("valor_minimo")), name="ck_serie_rango_valido"),
        ]
        indexes = [models.Index(fields=["sucursal", "tipo_documento", "activa"])]

    @staticmethod
    def _next_series(value):
        match = re.match(r"^(.*?)(\d+)$", value)
        if not match:
            raise ValidationError("La serie agotada no tiene un sufijo numérico incrementable.")
        prefix, digits = match.groups()
        return f"{prefix}{int(digits) + 1:0{len(digits)}d}"

    @classmethod
    def issue_next(cls, pk):
        with transaction.atomic():
            current = cls.objects.select_for_update().get(pk=pk, activa=True)
            issued_series = current.serie
            issued_number = current.valor_siguiente
            if issued_number > current.valor_maximo:
                raise ValidationError("El correlativo está fuera del rango configurado.")
            next_value = issued_number + current.incremento
            if next_value > current.valor_maximo:
                current.serie = cls._next_series(current.serie)
                current.valor_siguiente = current.valor_minimo
            else:
                current.valor_siguiente = next_value
            current.save(update_fields=["serie", "valor_siguiente", "updated_at"])
            return issued_series, issued_number
