# D7 — perfil de producción

## Estado

**NO EJECUTADO / NO VERIFICABLE.** El entorno actual no dispone de acceso autorizado read-only a PostgreSQL productivo. El mirror confirma estructura, pero tiene truncados varios catálogos esenciales.

Las consultas siguientes devuelven únicamente agregados. Deben ejecutarse dentro de una transacción read-only por infraestructura y revisarse antes de compartir su salida.

## Inventario y PK lógicas

```sql
BEGIN READ ONLY;
SET LOCAL statement_timeout = '120s';

WITH perfil(tabla, total, pk_distintas, pk_nulas, fecha_min, fecha_max) AS (
SELECT 'public.empresa' tabla, COUNT(*) total, COUNT(DISTINCT idempresa) pk_distintas,
       COUNT(*) FILTER (WHERE idempresa IS NULL) pk_nulas,
       NULL::date fecha_min, NULL::date fecha_max FROM public.empresa
UNION ALL
SELECT 'public.sucursal', COUNT(*), COUNT(DISTINCT idsucursal), COUNT(*) FILTER (WHERE idsucursal IS NULL),
       NULL::date, NULL::date FROM public.sucursal
UNION ALL
SELECT 'public.personal', COUNT(*), COUNT(DISTINCT idpersonal), COUNT(*) FILTER (WHERE idpersonal IS NULL),
       MIN(fechaingreso), MAX(fechaingreso) FROM public.personal
UNION ALL
SELECT 'public.vehiculo', COUNT(*), COUNT(DISTINCT idvehiculo), COUNT(*) FILTER (WHERE idvehiculo IS NULL),
       MIN(fechareg::date), MAX(fechareg::date) FROM public.vehiculo
UNION ALL
SELECT 'public.propietario', COUNT(*), COUNT(DISTINCT idpropietario), COUNT(*) FILTER (WHERE idpropietario IS NULL),
       MIN(fechaingreso), MAX(fechaingreso) FROM public.propietario
UNION ALL
SELECT 'public.transportista', COUNT(*), COUNT(DISTINCT idtransportista), COUNT(*) FILTER (WHERE idtransportista IS NULL),
       NULL::date, NULL::date FROM public.transportista
UNION ALL
SELECT 'public.recorridos', COUNT(*), COUNT(DISTINCT idrecorrido), COUNT(*) FILTER (WHERE idrecorrido IS NULL),
       NULL::date, NULL::date FROM public.recorridos
UNION ALL
SELECT 'comercial.linea', COUNT(*), COUNT(DISTINCT idlinea), COUNT(*) FILTER (WHERE idlinea IS NULL),
       NULL::date, NULL::date FROM comercial.linea
UNION ALL
SELECT 'transportes.manifiesto', COUNT(*), COUNT(DISTINCT idmanifiesto), COUNT(*) FILTER (WHERE idmanifiesto IS NULL),
       MIN(documentofecha), MAX(documentofecha) FROM transportes.manifiesto
UNION ALL
SELECT 'administrativo.papeleta', COUNT(*), COUNT(DISTINCT idpapeleta), COUNT(*) FILTER (WHERE idpapeleta IS NULL),
       MIN(documentofecha), MAX(documentofecha) FROM administrativo.papeleta
UNION ALL
SELECT 'public.cliente', COUNT(*), COUNT(DISTINCT idcliente), COUNT(*) FILTER (WHERE idcliente IS NULL),
       MIN(fechareg), MAX(fechareg) FROM public.cliente
)
SELECT *, total - pk_distintas - pk_nulas AS pk_duplicadas
FROM perfil
ORDER BY tabla;

ROLLBACK;
```

Clasificación esperada de identificadores:

| Entidad | Declaración conocida en mirror | Confirmación productiva |
|---|---|---|
| empresa | `idempresa`, PK declarativa no confirmada | Pendiente duplicados/nulos |
| sucursal | `idsucursal`, serial | Pendiente |
| personal | `idpersonal`, serial | Pendiente |
| vehículo | `idvehiculo`, serial | Pendiente |
| propietario | `idpropietario`, serial | Pendiente |
| conductor/transportista | `idtransportista`, serial | Pendiente de confirmar que esta sea la entidad funcional real |
| ruta/recorrido | `idrecorrido`, serial | Pendiente |
| línea | `comercial.linea.idlinea`, serial | Pendiente de confirmar frente a otras referencias legacy |
| manifiesto | `idmanifiesto`, serial | Pendiente |
| papeleta | `idpapeleta`, serial | PK respaldada por 7,259 filas del mirror; repetir en producción |
| cliente | `idcliente`, serial | PK respaldada por 417,405 filas del mirror; identidad documental no es única |

## Distribuciones de estados

Ejecutar un `GROUP BY` separado para evitar combinar semánticas:

```sql
BEGIN READ ONLY;
SELECT 'vehiculo' tabla, estado::text valor, COUNT(*) cantidad FROM public.vehiculo GROUP BY estado;
SELECT 'propietario' tabla, estado::text valor, COUNT(*) cantidad FROM public.propietario GROUP BY estado;
SELECT 'transportista' tabla, estado::text valor, COUNT(*) cantidad FROM public.transportista GROUP BY estado;
SELECT 'recorridos' tabla, estado::text valor, COUNT(*) cantidad FROM public.recorridos GROUP BY estado;
SELECT 'linea' tabla, estado::text valor, COUNT(*) cantidad FROM comercial.linea GROUP BY estado;
SELECT 'papeleta.estado' tabla, estado::text valor, COUNT(*) cantidad FROM administrativo.papeleta GROUP BY estado;
SELECT 'papeleta.estadopago' tabla, COALESCE(estadopago::text, '<NULL>') valor, COUNT(*) cantidad FROM administrativo.papeleta GROUP BY estadopago;
SELECT 'cliente' tabla, estado::text valor, COUNT(*) cantidad FROM public.cliente GROUP BY estado;
ROLLBACK;
```

## Integridad de relaciones fleet

Cada fila informa hijos, padres referenciados, vínculos válidos, huérfanos y porcentaje válido. No devuelve identificadores.

```sql
BEGIN READ ONLY;

SELECT 'vehiculo -> propietario' relacion,
       COUNT(*) hijos, COUNT(DISTINCT v.idpropietario) padres_referenciados,
       COUNT(p.idpropietario) validas,
       COUNT(*) FILTER (WHERE v.idpropietario IS NOT NULL AND p.idpropietario IS NULL) huerfanas,
       ROUND(100.0 * COUNT(p.idpropietario) / NULLIF(COUNT(*) FILTER (WHERE v.idpropietario IS NOT NULL), 0), 2) pct_valido
FROM public.vehiculo v LEFT JOIN public.propietario p ON p.idpropietario = v.idpropietario;

SELECT 'vehiculo -> clase' relacion,
       COUNT(*) hijos, COUNT(DISTINCT v.idclase) padres_referenciados,
       COUNT(c.idclase) validas,
       COUNT(*) FILTER (WHERE v.idclase IS NOT NULL AND c.idclase IS NULL) huerfanas,
       ROUND(100.0 * COUNT(c.idclase) / NULLIF(COUNT(*) FILTER (WHERE v.idclase IS NOT NULL), 0), 2) pct_valido
FROM public.vehiculo v LEFT JOIN public.clase c ON c.idclase = v.idclase;

SELECT 'vehiculo -> marca(public)' relacion,
       COUNT(*) hijos, COUNT(DISTINCT v.idmarca) padres_referenciados,
       COUNT(m.idmarca) validas,
       COUNT(*) FILTER (WHERE v.idmarca IS NOT NULL AND m.idmarca IS NULL) huerfanas,
       ROUND(100.0 * COUNT(m.idmarca) / NULLIF(COUNT(*) FILTER (WHERE v.idmarca IS NOT NULL), 0), 2) pct_valido
FROM public.vehiculo v LEFT JOIN public.marca m ON m.idmarca = v.idmarca;

SELECT 'vehiculo -> marca(comercial)' relacion,
       COUNT(*) hijos, COUNT(DISTINCT v.idmarca) padres_referenciados,
       COUNT(m.idmarca) validas,
       COUNT(*) FILTER (WHERE v.idmarca IS NOT NULL AND m.idmarca IS NULL) huerfanas,
       ROUND(100.0 * COUNT(m.idmarca) / NULLIF(COUNT(*) FILTER (WHERE v.idmarca IS NOT NULL), 0), 2) pct_valido
FROM public.vehiculo v LEFT JOIN comercial.marca m ON m.idmarca = v.idmarca;

SELECT 'vehiculo -> linea(comercial)' relacion,
       COUNT(*) hijos, COUNT(DISTINCT v.idlinea) padres_referenciados,
       COUNT(l.idlinea) validas,
       COUNT(*) FILTER (WHERE v.idlinea IS NOT NULL AND l.idlinea IS NULL) huerfanas,
       ROUND(100.0 * COUNT(l.idlinea) / NULLIF(COUNT(*) FILTER (WHERE v.idlinea IS NOT NULL), 0), 2) pct_valido
FROM public.vehiculo v LEFT JOIN comercial.linea l ON l.idlinea = v.idlinea;

SELECT 'vehiculo -> sucursal_fin' relacion,
       COUNT(*) hijos, COUNT(DISTINCT v.idsucursal_fin) padres_referenciados,
       COUNT(s.idsucursal) validas,
       COUNT(*) FILTER (WHERE v.idsucursal_fin IS NOT NULL AND s.idsucursal IS NULL) huerfanas,
       ROUND(100.0 * COUNT(s.idsucursal) / NULLIF(COUNT(*) FILTER (WHERE v.idsucursal_fin IS NOT NULL), 0), 2) pct_valido
FROM public.vehiculo v LEFT JOIN public.sucursal s ON s.idsucursal = v.idsucursal_fin;

SELECT 'manifiesto -> vehiculo' relacion,
       COUNT(*) hijos, COUNT(DISTINCT m.idvehiculo) padres_referenciados,
       COUNT(v.idvehiculo) validas,
       COUNT(*) FILTER (WHERE m.idvehiculo IS NOT NULL AND v.idvehiculo IS NULL) huerfanas,
       ROUND(100.0 * COUNT(v.idvehiculo) / NULLIF(COUNT(*) FILTER (WHERE m.idvehiculo IS NOT NULL), 0), 2) pct_valido
FROM transportes.manifiesto m LEFT JOIN public.vehiculo v ON v.idvehiculo = m.idvehiculo;

SELECT 'manifiesto -> recorrido' relacion,
       COUNT(*) hijos, COUNT(DISTINCT m.idrecorrido) padres_referenciados,
       COUNT(r.idrecorrido) validas,
       COUNT(*) FILTER (WHERE m.idrecorrido IS NOT NULL AND r.idrecorrido IS NULL) huerfanas,
       ROUND(100.0 * COUNT(r.idrecorrido) / NULLIF(COUNT(*) FILTER (WHERE m.idrecorrido IS NOT NULL), 0), 2) pct_valido
FROM transportes.manifiesto m LEFT JOIN public.recorridos r ON r.idrecorrido = m.idrecorrido;

SELECT 'manifiesto -> transportista candidato' relacion,
       COUNT(*) hijos, COUNT(DISTINCT m.idconductor) padres_referenciados,
       COUNT(t.idtransportista) validas,
       COUNT(*) FILTER (WHERE m.idconductor IS NOT NULL AND t.idtransportista IS NULL) huerfanas,
       ROUND(100.0 * COUNT(t.idtransportista) / NULLIF(COUNT(*) FILTER (WHERE m.idconductor IS NOT NULL), 0), 2) pct_valido
FROM transportes.manifiesto m LEFT JOIN public.transportista t ON t.idtransportista = m.idconductor;

SELECT 'papeleta -> vehiculo' relacion,
       COUNT(*) hijos, COUNT(DISTINCT p.idvehiculo) padres_referenciados,
       COUNT(v.idvehiculo) validas,
       COUNT(*) FILTER (WHERE p.idvehiculo IS NOT NULL AND v.idvehiculo IS NULL) huerfanas,
       ROUND(100.0 * COUNT(v.idvehiculo) / NULLIF(COUNT(*) FILTER (WHERE p.idvehiculo IS NOT NULL), 0), 2) pct_valido
FROM administrativo.papeleta p LEFT JOIN public.vehiculo v ON v.idvehiculo = p.idvehiculo;

-- Determina cuál catálogo corresponde a idinfractor sin exponer IDs.
SELECT 'papeleta.idinfractor candidato personal' candidato,
       COUNT(*) FILTER (WHERE p.idinfractor IS NOT NULL) referencias,
       COUNT(pe.idpersonal) coincidencias
FROM administrativo.papeleta p LEFT JOIN public.personal pe ON pe.idpersonal = p.idinfractor
UNION ALL
SELECT 'papeleta.idinfractor candidato transportista',
       COUNT(*) FILTER (WHERE p.idinfractor IS NOT NULL),
       COUNT(t.idtransportista)
FROM administrativo.papeleta p LEFT JOIN public.transportista t ON t.idtransportista = p.idinfractor;

ROLLBACK;
```

`vehiculo.modelo` es texto, no FK. No existe una relación `vehiculo → modelo` verificable en esta estructura. Tampoco existe una sucursal operativa directa inequívoca; solo se observa `idsucursal_fin`. Ambas diferencias deben resolverse antes de modelar.

## Resultado D7

**PENDIENTE DE EJECUCIÓN AUTORIZADA.** Mientras falten estos agregados, `fleet-core` puede diseñarse conceptualmente, pero no declararse listo para implementar.
