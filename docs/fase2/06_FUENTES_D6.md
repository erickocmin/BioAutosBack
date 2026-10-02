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

## Resultado productivo de Fase 2B

```text
Producción consultada: NO
reglasnegocio: NO DETERMINADO
logistica: NO DETERMINADO
caja: NO DETERMINADO
```

El script `scripts/audit/fleet_production_profile.py` incluye las consultas read-only de esquemas, servidores externos, extensiones y rutinas. Falta ejecutarlo con la cuenta autorizada.

## Alcanzabilidad local de referencias que afectan Fleet

| Referencia | Archivos | Funcionalidad | Fuente producción | Alcanzabilidad local | Estado |
|---|---:|---|---|---|---|
| `reglasnegocio.vehiculo` | 1 controlador | Anulación de vehículo | No determinada | Acción directa `vehiculoController::anular`; el resto del CRUD usa `public.vehiculo` | RUTA ALCANZABLE, referencia incoherente |
| `reglasnegocio.correlativos/documentos` | 4 modelos catálogo | Métodos de correlativo copiados en clase/color/marca/modelo | No determinada | Acciones públicas existen, pero no se encontró navegación/JS que invoque esos métodos; los CRUD apuntan además a tablas inexistentes | CÓDIGO PROBABLEMENTE MUERTO |
| `reglasnegocio.v_sucursal` | 1 controlador | Filtro de rotativo masivo | No determinada | Acción/controlador existe; la vista masiva ya estaba documentada como faltante/incompleta | NO DETERMINADO |
| `logistica.area_oficina` | 1 controlador | Combos de edición de rotativo | No determinada | Acción de edición existe; depende de fuente ausente | RUTA ALCANZABLE, fuente no determinada |
| `reglasnegocio.guia/dtguia` | 1 modelo | Reasignación/consulta de rezagados | No determinada | Métodos de rezagados referencian la fuente; pertenece a cargo, no a fleet-core básico | RUTA ALCANZABLE fuera de fleet-core |

## Separación modelo válido / PHP roto

- `public.vehiculo` es la fuente usada por el CRUD y consultas operativas; una referencia errónea en `anular` no invalida automáticamente la entidad.
- El conductor se resuelve en código activo contra `public.transportista`, tanto desde vehículos como manifiestos.
- El formulario operativo usa `public.clase`, `public.v_color` y `public.v_marca`; los controladores `vehiculoclase/color/marca/modelo` apuntan a tablas distintas ausentes y son candidatos a no migrar.
- El flujo activo de vehículo consulta `public.lineas`; `comercial.linea` es una entidad paralela usada por inventario. La evidencia productiva debe confirmar la integridad del vínculo.

Estas conclusiones reducen el alcance de D6: las referencias rotas no bloquean por sí solas toda entidad `Vehicle`, pero D7 sigue siendo necesario para confirmar datos y relaciones reales.
