# D17 — fuentes de `estadocta` y `presupuestos`

## Resultado de investigación estática

La premisa original se corrige parcialmente con evidencia directa del código:

### `administrativo.estadocta`

- `model/regfactura.php` crea y actualiza filas mediante `__dbMantenimiento(..., "administrativo.estadocta", 1|2)`.
- El mismo modelo realiza baja lógica con `UPDATE ... SET estado=0`.
- `model/cheques.php` y `model/garantia_dev.php` actualizan cheque, importe pagado y estado de filas existentes.
- Existen lecturas adicionales en consultas, reportes y vistas.

Clasificación: **ACTIVA EN CÓDIGO LEGACY**, pendiente de confirmar uso productivo y frecuencia.

### `administrativo.presupuestos`

- Se lee como catálogo desde cheques y garantía.
- El módulo/controlador llamado `presupuestos` no escribe esa tabla: administra `administrativo.areagrupo`.
- No se encontró `INSERT`, `UPDATE` o `DELETE` local sobre `administrativo.presupuestos`.

Clasificación: **NO DETERMINADO**. Puede provenir de carga manual, batch, otro sistema o datos históricos.

## Verificación read-only para producción

```sql
BEGIN READ ONLY;

SELECT 'administrativo.estadocta' tabla,
       COUNT(*) filas,
       MIN(documentofecha) fecha_min,
       MAX(documentofecha) fecha_max
FROM administrativo.estadocta
UNION ALL
SELECT 'administrativo.presupuestos',
       COUNT(*),
       NULL::date,
       NULL::date
FROM administrativo.presupuestos;

SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE (schemaname, tablename) IN (
    ('administrativo', 'estadocta'),
    ('administrativo', 'presupuestos')
);

SELECT event_object_schema, event_object_table, trigger_name,
       event_manipulation, action_timing
FROM information_schema.triggers
WHERE (event_object_schema, event_object_table) IN (
    ('administrativo', 'estadocta'),
    ('administrativo', 'presupuestos')
)
ORDER BY event_object_table, trigger_name;

ROLLBACK;
```

Para atribuir escritores reales se necesitan logs de auditoría/conexiones o telemetría productiva; una fotografía de `current_user` no reconstruye autores históricos.

## Resultado D17

**PARCIALMENTE RESUELTA POR EVIDENCIA TÉCNICA.** `estadocta` tiene escritor localizado; `presupuestos` sigue pendiente. Solo bloquea la migración de esas capacidades de treasury/hr.
