# D16 — identidad de clientes

## Evidencia del mirror

- Clientes totales: 417,405.
- Sin DNI o con DNI vacío: 148,269 (35.5%).
- DNI no vacío: 269,136 filas.
- DNI distintos no vacíos: 165,671.
- Existen documentos repetidos entre diferentes `idcliente`.

Estas cifras no permiten concluir que todas las repeticiones sean duplicados: pueden mezclar personas, empresas, representantes o errores de captura.

## Consulta estadística de producción

No devuelve documentos ni nombres.

```sql
BEGIN READ ONLY;
SET LOCAL statement_timeout = '120s';

WITH base AS (
    SELECT
        idcliente,
        idtipodocumentos,
        NULLIF(BTRIM(dni), '') AS dni_norm,
        NULLIF(BTRIM(ruc), '') AS ruc_norm
    FROM public.cliente
), dni_groups AS (
    SELECT dni_norm, COUNT(*) cantidad
    FROM base
    WHERE dni_norm IS NOT NULL
    GROUP BY dni_norm
), ruc_groups AS (
    SELECT ruc_norm, COUNT(*) cantidad
    FROM base
    WHERE ruc_norm IS NOT NULL
    GROUP BY ruc_norm
)
SELECT
    (SELECT COUNT(*) FROM base) AS clientes_totales,
    (SELECT COUNT(*) FROM base WHERE dni_norm IS NULL) AS sin_dni,
    (SELECT COUNT(*) FROM base WHERE dni_norm IS NOT NULL AND dni_norm !~ '^[0-9]{8}$') AS dni_formato_invalido,
    (SELECT COUNT(*) FROM dni_groups WHERE cantidad > 1) AS valores_dni_repetidos,
    (SELECT COALESCE(SUM(cantidad), 0) FROM dni_groups WHERE cantidad > 1) AS filas_en_grupos_dni_repetido,
    (SELECT COUNT(*) FROM base WHERE ruc_norm IS NULL) AS sin_ruc,
    (SELECT COUNT(*) FROM base WHERE ruc_norm IS NOT NULL AND ruc_norm !~ '^[0-9]{11}$') AS ruc_formato_invalido,
    (SELECT COUNT(*) FROM ruc_groups WHERE cantidad > 1) AS valores_ruc_repetidos,
    (SELECT COALESCE(SUM(cantidad), 0) FROM ruc_groups WHERE cantidad > 1) AS filas_en_grupos_ruc_repetido;

SELECT idtipodocumentos, COUNT(*) AS cantidad
FROM public.cliente
GROUP BY idtipodocumentos
ORDER BY idtipodocumentos;

ROLLBACK;
```

## Opciones de diseño para la sesión

- Unicidad condicional solo para documentos normalizados y tipos que realmente deban ser únicos.
- Proceso de deduplicación previo, sin fusión automática.
- Merge auditado que conserve IDs legacy y relaciones históricas.
- Clientes sin documento mediante un identificador interno, sin valores ficticios compartidos.
- Separar persona y empresa cuando el proceso confirme que DNI, RUC y representante son conceptos distintos.

## Recomendación técnica

No aplicar `UNIQUE DNI`. Normalizar `tipo + número`, conservar `legacy_id/legacy_source` y exigir revisión humana para fusionar identidades.

## Resultado D16

**PENDIENTE DE NEGOCIO Y PERFILADO PRODUCTIVO.** Bloquea identidad de pasajeros/clientes en `ticketing` y `cargo`, no los catálogos de flota.
