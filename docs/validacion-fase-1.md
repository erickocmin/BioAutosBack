# Validación de Fase 1

Checkpoint local del 20 de septiembre de 2026:

- MySQL Community Server 8.0.46, base `sisgetran_dev`.
- 44 tablas físicas: 44 InnoDB y 44 con collation `utf8mb4_0900_ai_ci`.
- 44 PK, 61 FK, 40 restricciones UNIQUE y 16 CHECK.
- Migraciones Django aplicadas hasta `inventory.0003`; `check` y `makemigrations --check` limpios.
- Suite backend: 32 pruebas en SQLite y las mismas 32 en MySQL, incluyendo aislamiento anti-IDOR por empresa/sucursal.
- ZKTeco: handshake, ATTLOG, reenvío idempotente, empleado, dato crudo, procesamiento y agregado diario verificados en MySQL.
- Integración Playwright: login React/JWT y recorrido de módulos verdes; compra, salida, traslado y arqueo/cierre ejecutados contra Django y MySQL.
- Dominios bloqueados y no implementados: `ticketing`, `fleet`, `cargo`, `billing` (`BLOCKED_DOMAIN`).

La medición local de listados representativos arrojó 7–10 consultas por endpoint, 8–17 ms y payloads de 253–2973 bytes con el conjunto ficticio de integración. Incluye JWT, permisos y resolución de ámbito; son cifras orientativas, no un benchmark de carga.
