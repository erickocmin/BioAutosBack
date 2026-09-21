# D6 — fuentes y esquemas ausentes

## Evidencia local

El catálogo completo del mirror no contiene los esquemas `reglasnegocio`, `logistica` ni `caja`. La búsqueda estática encontró referencias distribuidas así:

| Referencia | Archivos con coincidencias | Evidencia de conexión separada en el repositorio | Clasificación actual |
|---|---:|---|---|
| `reglasnegocio.*` | 41 | No encontrada | NO DETERMINADO |
| `logistica.*` | 6 | No encontrada | NO DETERMINADO |
| `caja.*` | 16 | No encontrada; una coincidencia pertenece a una librería JS | NO DETERMINADO |

También se buscaron DSN adicionales, `dblink`, FDW, servidores federados, jobs y scripts. El código usa conexiones PostgreSQL directas, pero no aporta evidencia de una segunda fuente específica para esos esquemas. La auditoría previa confirmó que en el mirror no existen `dblink`, FDW, triggers de evento ni extensiones de integración que los suministren.

## Lectura técnica

- Varias referencias aparecen dentro de métodos activos, por lo que no se pueden etiquetar globalmente como código muerto solo por inspección estática.
- Contra el mirror auditado esas rutas fallarían porque los esquemas no existen.
- No hay evidencia local suficiente para clasificarlas como `ACTIVA` o `SISTEMA EXTERNO` en producción.
- La hipótesis de código heredado de un sistema hermano es consistente, pero sigue siendo hipótesis.

## Verificación read-only para producción

```sql
BEGIN READ ONLY;

SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('reglasnegocio', 'logistica', 'caja')
ORDER BY schema_name;

SELECT foreign_server_name, foreign_data_wrapper_name
FROM information_schema.foreign_servers
ORDER BY foreign_server_name;

SELECT extname
FROM pg_extension
WHERE extname IN ('dblink', 'postgres_fdw');

SELECT routine_schema, routine_name
FROM information_schema.routines
WHERE routine_definition ILIKE ANY (ARRAY['%reglasnegocio%', '%logistica.%', '%caja.%'])
ORDER BY routine_schema, routine_name;

ROLLBACK;
```

Además, infraestructura debe revisar fuera de la base: cron, Task Scheduler, servicios, variables del despliegue, repositorios del proveedor y logs de conexiones. No se deben compartir connection strings ni secretos.

## Criterio por referencia

- `ACTIVA`: ejecución productiva y fuente de datos demostradas.
- `SISTEMA EXTERNO`: propietario, interfaz y evidencia de intercambio identificados.
- `LEGACY`: fuente histórica confirmada, sin uso actual pero con datos a conservar.
- `CÓDIGO MUERTO`: ruta no alcanzable y sin uso confirmada por operación/telemetría.
- `NO DETERMINADO`: falta evidencia productiva.

## Resultado D6

**PARCIALMENTE RESUELTA.** Está confirmado que los esquemas faltan en el mirror y que el repositorio no define una fuente alternativa; su naturaleza productiva sigue `NO DETERMINADA`. Bloquea las capacidades que dependen de esas tablas, no todos los catálogos independientes por definición.
