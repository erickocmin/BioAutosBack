# D2 — series y correlativos de producción

## Estado

**NO VERIFICABLE desde este entorno.** No existe una conexión autorizada read-only a producción. El mirror contiene cero filas en `public.tipodocumentocorrelativo`, por lo que no permite medir el riesgo actual.

No se utilizaron las credenciales expuestas en el legacy.

## Consulta exacta para infraestructura

Ejecutar con un rol PostgreSQL de solo lectura. La consulta no contiene DDL ni DML y no devuelve datos personales.

```sql
BEGIN READ ONLY;
SET LOCAL statement_timeout = '30s';

SELECT
    c.idcorrelativo,
    c.idtipodocumento,
    COALESCE(t.abreviatura, t.descripcion, c.descripcion) AS documento,
    c.serie,
    c.valorsiguiente AS actual,
    c.valormaximo AS maximo,
    c.valormaximo - c.valorsiguiente AS restante,
    c.estado,
    CASE
        WHEN c.valorsiguiente > c.valormaximo THEN 'AGOTADA'
        WHEN c.valorsiguiente = c.valormaximo THEN 'CRITICA'
        WHEN c.valormaximo - c.valorsiguiente <= 100 THEN 'CRITICA'
        WHEN c.valormaximo - c.valorsiguiente <= 1000 THEN 'ADVERTENCIA'
        ELSE 'OK'
    END AS clasificacion,
    NULL::date AS ultima_fecha_utilizacion_no_determinada
FROM public.tipodocumentocorrelativo AS c
LEFT JOIN public.tipodocumento AS t
  ON t.idtipodocumento = c.idtipodocumento
ORDER BY
    CASE
        WHEN c.valorsiguiente >= c.valormaximo THEN 0
        WHEN c.valormaximo - c.valorsiguiente <= 100 THEN 1
        WHEN c.valormaximo - c.valorsiguiente <= 1000 THEN 2
        ELSE 3
    END,
    c.idtipodocumento,
    c.serie;

ROLLBACK;
```

`ultima_fecha_utilizacion` queda deliberadamente sin inferir: la auditoría no confirmó una relación única y fiable entre cada serie y su tabla emisora. Infraestructura debe añadirla desde logs o desde la fuente de emisión confirmada, no mediante una suposición por formato del documento.

## Plantilla de resultado

| Documento | Serie | Actual | Máximo | Restante | Estado | Último uso |
|---|---:|---:|---:|---:|---|---|
| Pendiente de ejecución | — | — | — | — | NO VERIFICABLE | — |

Los umbrales 100/1000 sirven para priorización operativa, no constituyen una regla tributaria. El responsable de facturación debe aprobar otros umbrales si el volumen diario los vuelve insuficientes.

## Resultado D2

**PENDIENTE DE EVIDENCIA TÉCNICA.** Bloquea `billing.series` y `billing.correlatives`, pero no bloquea catálogos independientes de otros dominios.
