# Handoff para Infraestructura — perfil D7 de Fleet

## Propósito

Validar únicamente estructura, volumen e integridad agregada de `fleet-core` contra PostgreSQL productivo, sin modificar datos, esquema, estadísticas, configuración ni secuencias.

La ejecución permitirá confirmar claves, estados, relaciones y cardinalidades de Vehicle, Owner, Driver, Route, Line, VehicleDocument y Manifest. No implementa Fleet ni resuelve reglas de papeletas o deuda.

## Qué no hará el paquete

```text
NO INSERT
NO UPDATE
NO DELETE
NO ALTER
NO CREATE
NO DROP
NO TRUNCATE
NO GRANT/REVOKE
NO ANALYZE/VACUUM
NO extracción de datos personales
```

El script no selecciona DNI, RUC individual, placa, nombres, apellidos, dirección, teléfono ni correo.

## Archivos del paquete

```text
scripts/audit/fleet_production_profile.py
requirements/audit.txt
docs/fase2/17_HANDOFF_INFRA_D7.md
```

El script contiene el perfil D7 y la metadata agregada de D6; no es necesario ejecutar SQL adicional.

## Cuenta requerida

Utilizar una cuenta temporal o permanente administrada por Infraestructura con:

- `CONNECT` únicamente sobre la base objetivo.
- `USAGE` sobre `public`, `comercial`, `transportes` y `administrativo`.
- `SELECT` únicamente sobre las tablas listadas abajo.
- Acceso de lectura normal a `information_schema` y la metadata requerida de `pg_catalog`.

La cuenta no debe ser:

- superusuario;
- propietaria de la base, esquemas o tablas;
- miembro de roles con escritura;
- capaz de `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `CREATE` o mantenimiento.

El script aborta si detecta superusuario; privilegios `INSERT`, `UPDATE`, `DELETE` o `TRUNCATE` sobre tablas visibles; o privilegios `CREATE` sobre la base/esquemas auditados.

### Alcance de esta verificación

La comprobación automática cubre superusuario, DML/`TRUNCATE` efectivos sobre las tablas visibles y `CREATE` sobre la base/esquemas auditados. PostgreSQL puede tener funciones `SECURITY DEFINER`, permisos sobre otros objetos o integraciones externas cuya ausencia absoluta no puede demostrarse solo con estas funciones de privilegios.

La defensa es acumulativa:

```text
cuenta dedicada read-only
+ BEGIN READ ONLY
+ queries estáticas SELECT/WITH/SHOW
+ validación de privilegios
+ ROLLBACK obligatorio
```

No se afirma que un chequeo aislado garantice por sí solo imposibilidad absoluta de escritura indirecta.

## Tablas utilizadas realmente por el script

### `public`

```text
empresa
sucursal
personal
vehiculo
propietario
transportista
recorridos
lineas
cliente
clase
color
marca
vehiculochoferes
```

### `comercial`

```text
linea
marca
```

### `transportes`

```text
manifiesto
vehiculo_carroceria
vehiculo_permisos
```

Si `transportes.vehiculo_modelo` existe, el script ejecuta además una comparación agregada de correspondencia con `vehiculo.modelo`. Si no existe, la consulta se omite de forma segura.

### `administrativo`

```text
papeleta
```

### Metadata

```text
information_schema.tables
information_schema.columns
information_schema.schemata
information_schema.foreign_servers
information_schema.routines
pg_catalog.pg_extension
pg_catalog.pg_user
```

No solicitar acceso a tablas adicionales “por si acaso”. Si falta un permiso, devolver el código controlado del error para revisar el alcance; no ampliar privilegios automáticamente.

## Dependencia mínima

El único paquete externo es:

```text
psycopg[binary]>=3.2,<4
```

Está aislado en `requirements/audit.txt`. Se recomienda un entorno virtual temporal fuera del checkout de producción.

Ejemplo:

```bash
python -m venv /ruta/temporal/sisgetran-fleet-audit
/ruta/temporal/sisgetran-fleet-audit/bin/python -m pip install --requirement requirements/audit.txt
```

En Windows:

```powershell
py -m venv C:\ruta\temporal\sisgetran-fleet-audit
C:\ruta\temporal\sisgetran-fleet-audit\Scripts\python.exe -m pip install --requirement requirements\audit.txt
```

No se instala ninguna dependencia en el runtime de SISGETRAN.

## Variables de entorno exactas

`FLEET_AUDIT_EXPECTED_DATABASE` siempre es obligatoria y evita ejecutar accidentalmente sobre otra base.

### Opción 1 — DSN inyectado por un gestor de secretos

```text
FLEET_AUDIT_DSN
FLEET_AUDIT_EXPECTED_DATABASE
```

### Opción 2 — variables separadas

```text
FLEET_AUDIT_HOST
FLEET_AUDIT_PORT
FLEET_AUDIT_DATABASE
FLEET_AUDIT_USER
FLEET_AUDIT_PASSWORD
FLEET_AUDIT_SSLMODE
FLEET_AUDIT_EXPECTED_DATABASE
```

Requeridas en la opción 2: host, base, usuario y contraseña. Puerto predeterminado: `5432`. `sslmode` predeterminado: `require`.

Si se proporciona `FLEET_AUDIT_DSN`, esa opción tiene precedencia. No imprimir, registrar ni enviar estas variables. Inyectarlas desde el mecanismo seguro aprobado por Infraestructura; no escribir la contraseña en el historial del shell.

## Self-test previo

Ejecutar sin conexión:

```bash
python scripts/audit/fleet_production_profile.py --self-test
```

Resultado esperado:

```text
SELF-TEST OK: sin DML/DDL/PII/SELECT *, BEGIN READ ONLY, timeout, ROLLBACK y salida agregada validados
```

El self-test verifica:

- allowlist `SELECT`, `WITH` y `SHOW` para las consultas del perfil;
- ausencia de DML y DDL;
- ausencia de selección explícita de columnas PII conocidas;
- prohibición de `SELECT *`;
- `BEGIN READ ONLY`;
- configuración de `statement_timeout`;
- `ROLLBACK`;
- salida agregada sin patrones de secreto.

## Paso 1 — mirror

Inyectar variables para el mirror y ejecutar exactamente el mismo archivo:

```bash
python scripts/audit/fleet_production_profile.py \
  --format markdown \
  --output fleet-mirror-profile.md
```

Windows PowerShell:

```powershell
python scripts\audit\fleet_production_profile.py --format markdown --output fleet-mirror-profile.md
```

Revisar:

- salida exitosa, código `0`;
- base esperada correcta;
- `transaction_read_only=true`;
- cero tablas con privilegios DML/`TRUNCATE` y cero privilegios `CREATE` en el alcance;
- únicamente conteos, estados y metadata agregada;
- ninguna PII.

```text
MIRROR ≠ PRODUCCIÓN
```

El mirror valida dependencias, compatibilidad y formato, pero no cierra D7.

## Paso 2 — producción

Tras aprobar la ejecución del mirror, inyectar la cuenta productiva read-only y ejecutar el mismo script sin modificar queries:

```bash
python scripts/audit/fleet_production_profile.py \
  --format markdown \
  --output fleet-production-profile.md
```

Windows PowerShell:

```powershell
python scripts\audit\fleet_production_profile.py --format markdown --output fleet-production-profile.md
```

El timeout predeterminado es 60 segundos por sentencia. Solo si Infraestructura lo aprueba puede cambiarse, dentro del rango soportado:

```bash
python scripts/audit/fleet_production_profile.py --timeout-ms 120000 --format markdown --output fleet-production-profile.md
```

Argumentos soportados:

| Argumento | Valores | Predeterminado |
|---|---|---|
| `--self-test` | flag | desactivado |
| `--format` | `json`, `markdown` | `json` |
| `--output` | ruta | stdout |
| `--timeout-ms` | 1000–300000 | 60000 |

## Resultados mínimos incluidos

### Vehicle

- total, PK distinta/nula/duplicada y fechas;
- distribución de estados;
- propietario, clase, marca, línea y `idsucursal_fin` agregados;
- matches, huérfanos y porcentajes;
- nulidad y cardinalidad de `modelo`, sin listar valores.

### Owner

- total, PK y estados;
- propietarios referenciados;
- propietarios con uno o varios vehículos;
- máximo y promedio agregado de vehículos.

### Driver

- totales de transportista y personal;
- matches agregados de manifiesto y vehículo contra ambos candidatos;
- comparación agregada de infractor, sin documentos ni nombres.

### Route

- total, PK, estados, origen/destino nulos;
- pares origen/destino duplicados;
- uso y matches en manifiestos.

### Line

- total y PK de `public.lineas` y `comercial.linea`;
- vehículos con línea;
- matches y huérfanos contra ambos catálogos.

### VehicleDocument

- cobertura agregada de SOAT, revisión técnica, permisos, contratos y licencia;
- existencia de catálogos operativos y huérfanos relevantes.

### Manifest

- total, PK, fechas y presencia de numeración;
- relaciones agregadas con vehículo, recorrido y transportista;
- comprobación de existencia de columna de estado.

### Papeletas y D6

- matriz `estado × estadopago`, sin semántica inventada;
- relaciones agregadas;
- existencia de `reglasnegocio`, `logistica` y `caja`;
- metadata de foreign servers, `dblink`/`postgres_fdw` y rutinas relacionadas.

## Códigos de salida

| Código | Significado |
|---:|---|
| 0 | Ejecución o self-test correctos |
| 2 | Bloqueo controlado: variables, base esperada, read-only, privilegios o query |
| 3 | Fallo inesperado sin imprimir detalles de conexión |

Los mensajes de error están deliberadamente redactados. No enviar logs del driver ni repetir la ejecución con credenciales en línea de comandos.

## Revisión antes de entregar el resultado

- [ ] El archivo corresponde a producción, no al mirror.
- [ ] No contiene DSN, usuario, contraseña, host completo ni variables de entorno.
- [ ] No contiene DNI, RUC individual, placa, nombres, direcciones, teléfonos o correos.
- [ ] Solo contiene agregados y metadata necesaria.
- [ ] Se revisó si nombres de servidores externos/rutinas son metadata sensible; si lo son, se redactan conservando conteos y conclusión D6.
- [ ] No se adjunta dump, CSV de personas, backup, captura de consola ni archivo `.env`.
- [ ] El resultado no se agrega a Git antes de una segunda revisión de seguridad.

Los nombres de salida recomendados están incluidos en `.gitignore` como defensa contra commits accidentales. Si posteriormente se aprueba una versión redactada, deberá agregarse de forma explícita y consciente.

## Entrega solicitada

Devolver únicamente:

```text
fleet-production-profile.md
```

El resultado agregado de D6 ya está incluido dentro del mismo archivo. Si se prefiere JSON, devolver `fleet-production-profile.json` en lugar del Markdown, no ambos salvo necesidad operativa.

No necesitamos acceso directo, contraseña, dump ni backup. Infraestructura puede ejecutar todo localmente y compartir solo la salida revisada.

## Qué ocurrirá después

El equipo de migración actualizará:

```text
docs/fase2/05_PERFIL_PRODUCCION.md
docs/fase2/06_FUENTES_D6.md
docs/fase2/16_FLEET_READINESS.md
```

Se reevaluarán por separado Vehicle, Owner, Driver, Route, Line, VehicleDocument y manifest-core. `manifest-numbering` seguirá bloqueado por D2, papeletas por D13 y debt-validation por D10/D13/D15.

No se implementará `apps/fleet` automáticamente después de recibir el archivo.

## Mensaje listo para enviar a Infraestructura

> Necesitamos validar únicamente la estructura e integridad agregada de los catálogos de Fleet de SISGETRAN en PostgreSQL productivo. Adjuntamos un script que ejecuta consultas estáticas `SELECT/WITH/SHOW` dentro de `BEGIN READ ONLY`, aplica timeout, verifica que la cuenta no sea superusuario ni tenga privilegios DML, `TRUNCATE` o `CREATE` en el alcance auditado y finaliza con `ROLLBACK`. No selecciona DNI, RUC, placas, nombres, direcciones, teléfonos ni correos. Infraestructura puede crear una cuenta dedicada con `CONNECT`, `USAGE` y `SELECT` mínimos, ejecutar primero el self-test y el mirror, y luego producción. Solo necesitamos que nos devuelvan `fleet-production-profile.md` revisado; no necesitamos contraseña, dump, backup ni acceso de escritura. Por favor no incluyan variables de entorno, logs de conexión ni capturas con secretos.

## Estado

```text
FASE 2C PREPARADA — PENDIENTE EJECUCIÓN DE INFRAESTRUCTURA
```
