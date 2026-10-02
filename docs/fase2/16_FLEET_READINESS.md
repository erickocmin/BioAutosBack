# Fleet readiness — Fase 2B

Fecha de preparación: 20 de septiembre de 2026.

## Estado de la ejecución

No existe una cuenta PostgreSQL productiva read-only autorizada en este entorno. En cumplimiento de la regla de seguridad, no se usaron las credenciales hardcodeadas del legacy y no se intentó conectar a producción.

La evidencia nueva de esta fase es:

- un script agregado y con guardas read-only;
- análisis de alcance de las referencias D6;
- confirmación estática de las fuentes que usa el PHP activo;
- criterios exactos que debe satisfacer la ejecución productiva.

No constituye cierre de D7.

## Matriz de capacidades

| Capacidad | Modelo | Fuente | Relaciones | Reglas | Estado |
|---|---|---|---|---|---|
| `fleet.catalogs` | Clase, color, marca, carrocería y modelo aún requieren normalización conceptual | El formulario activo usa `public.clase`, `public.v_color`, `public.v_marca`; carrocería combina texto/ID; modelo es texto | Debe medirse integridad desde vehículo | CRUD huérfanos no se migrarán por nombre | 🟡 PARCIAL |
| `fleet.vehicles` | Estructura de `public.vehiculo` confirmada | `public.vehiculo` es la fuente del CRUD activo | Propietario/catálogos/línea/sucursal_fin pendientes de medición productiva | Estado y campos principales conocidos; no incluye deuda | 🟡 PARCIAL |
| `fleet.owners` | `public.propietario` documentado | Fuente usada por vehículo y reportes | Cardinalidad 1:N e integridad pendientes de producción | Estado estructural conocido | 🟡 PARCIAL |
| `fleet.drivers` | Código activo modela conductor como `public.transportista` | `conductores`, vehículo y manifiesto consultan `public.transportista` | `vehiculochoferes` y manifiesto deben confirmar matches productivos | No se equipara con `personal` sin resultado estadístico | 🟡 PARCIAL |
| `fleet.documents` | SOAT/revisión en vehículo; licencia en transportista; permisos en `transportes.vehiculo_permisos` | Fuentes estructurales identificadas | Relaciones y cobertura pendientes de producción | Bloqueo por deuda excluido | 🟡 PARCIAL |
| `fleet.routes` | `public.recorridos` con origen/destino | Controlador/modelo activo | Uso por manifiestos y posibles duplicados pendientes | Estado estructural conocido | 🟡 PARCIAL |
| `fleet.lines` | Línea de transporte separada de línea de inventario | El modelo activo de vehículo une `idlinea` con `public.lineas`; `comercial.linea` es paralela | Match y huérfanos pendientes de producción | No fusionar catálogos por nombre | 🟡 PARCIAL |
| `fleet.manifest-core` | Cabecera/detalle conocidos | `transportes.manifiesto` y detalle | Vehículo/ruta/conductor pendientes de producción | Sin lógica SUNAT ni numeración | 🟡 PARCIAL |
| `fleet.manifest-numbering` | Correlativo documental | `tipodocumentocorrelativo` | Depende de serie/sucursal | D2 pendiente | 🔴 BLOQUEADO |
| `fleet.papeletas` | Estructura y matriz conocidas | `administrativo.papeleta` | Relaciones productivas pendientes | Semántica D13 pendiente | 🔴 BLOQUEADO |
| `fleet.debt-validation` | Doce verificaciones legacy reconstruidas | Múltiples fuentes | No se diseña en esta fase | D10, D13 y D15 pendientes | 🔴 BLOQUEADO |

## Hallazgos de código que orientan el perfil

### Vehicle

- El CRUD operativo usa `public.vehiculo`.
- `modelo` y `carroceria` existen como texto; también existe `idcarroceria`.
- No se creará una FK de modelo sin que producción demuestre un catálogo real y correspondencia suficiente.
- La acción legacy `anular` consulta erróneamente `reglasnegocio.vehiculo`; ese defecto del PHP no invalida el modelo principal.

### Owner

- `public.vehiculo.idpropietario` enlaza con `public.propietario` en consultas activas.
- Falta confirmar huérfanos y cuántos propietarios tienen uno o varios vehículos.

### Driver

- `model/conductores.php` administra `public.transportista`.
- `model/vehiculo.php` enlaza `vehiculochoferes.idchofer` con `transportista.idtransportista`.
- `model/manifiesto.php` enlaza `manifiesto.idconductor` con `transportista.idtransportista`.
- Esto favorece `CONDUCTOR = transportista`, pero el verde exige que los agregados productivos confirmen los matches frente a `personal`.

### Route

- `public.recorridos` contiene origen y destino y es consumida por rutas/manifiestos.
- Falta validar volumen, estados, pares duplicados y referencias reales.

### Line

- El PHP operativo de vehículos usa `public.lineas`.
- `comercial.linea` pertenece al catálogo de productos/inventario y no debe fusionarse automáticamente.
- Producción debe confirmar qué tabla explica realmente `vehiculo.idlinea`.

### VehicleDocument

- SOAT: fechas de expedición/caducidad en `public.vehiculo`.
- Revisión técnica: fechas de expedición/caducidad en `public.vehiculo`.
- Permisos: `transportes.vehiculo_permisos` con vehículo, región, tipo y vencimiento.
- Licencia: `public.transportista.fecvencimiento`.
- Las pantallas auxiliares de vencimientos tienen referencias legacy inconsistentes; el modelo nuevo debe usar las fuentes confirmadas, no copiar esas consultas.

### Sucursal del vehículo

`idsucursal_fin` es actualizado por `model/tikectsalida.php` usando el destino de la operación. La evidencia de código no permite llamarlo “sucursal operativa” ni “sucursal financiera”; parece representar una ubicación/destino final mutable. Clasificación actual: **OTRA SEMÁNTICA / NO DETERMINADA**, pendiente de distribución productiva y confirmación operativa.

### Manifest

- El core usa manifiesto, vehículo, recorrido y transportista.
- La estructura auditada no declara una columna `estado`; el script comprueba esta ausencia en producción.
- La numeración se separa como `fleet.manifest-numbering`, bloqueada por D2.

## Comparación antes/después

| Subdominio | Antes | Después | Razón |
|---|---|---|---|
| catalogs | 🟡 | 🟡 | Fuentes activas mejor delimitadas; faltan integridad/volumen productivos |
| vehicles | 🟡 | 🟡 | Fuente principal confirmada por código; D7 no ejecutada |
| owners | 🟡 | 🟡 | Relación conocida; cardinalidad productiva pendiente |
| drivers | 🟡 | 🟡 | `transportista` es candidato fuerte; falta confirmación con datos reales |
| documents | 🟡 | 🟡 | Fuentes separadas identificadas; cobertura productiva pendiente |
| routes | 🟡 | 🟡 | Fuente conocida; D7 no ejecutada |
| lines | 🟡 | 🟡 | `public.lineas` es candidato operativo; match productivo pendiente |
| manifests | 🟡 | 🟡/🔴 | Core amarillo; numeración separada en rojo por D2 |
| papeletas | 🔴 | 🔴 | D13 no se resuelve técnicamente |
| debt-validation | 🔴 | 🔴 | D10/D13/D15 permanecen fuera |

## Evidencia suficiente para diseñar modelos

| Modelo | Evidencia suficiente hoy | Evidencia restante |
|---|---|---|
| `Vehicle` | No | Perfil productivo, integridad de catálogos/owner/línea y semántica de ubicación |
| `Owner` | No | PK/estados/cardinalidad productivos |
| `Driver` | No | Matches productivos que confirmen `transportista` frente a `personal` |
| `Route` | No | Volumen, estados, origen/destino y uso por manifiestos |
| `Line` | No | Correspondencia de `idlinea` con `public.lineas` y descarte de `comercial.linea` |
| `VehicleDocument` | No | Cobertura, relaciones y estados productivos de cada fuente |
| `Manifest` | No | PK/volumen/relaciones productivas; numeración queda separada |

## Único conjunto de evidencia restante

1. Una cuenta autorizada que no sea superusuario y tenga cero privilegios DML en los esquemas auditados.
2. Ejecución satisfactoria del script primero contra el mirror y después contra producción.
3. Entrega del JSON/Markdown agregado revisado, sin PII.
4. Confirmación operativa de la semántica de `idsucursal_fin` si los datos por sí solos no la cierran.

## Primer incremento implementable

```text
FLEET-CORE SIGUE BLOQUEADO
```

No hay un modelo con todos los criterios verdes mientras D7 no haya sido ejecutada. El primer incremento candidato sigue siendo `Vehicle + Owner + Driver + Route + Line + VehicleDocument`, excluyendo manifiesto-numbering, papeletas y debt-validation.
