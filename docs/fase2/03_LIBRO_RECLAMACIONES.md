# D3 — Libro de Reclamaciones

## Pregunta para operaciones

> ¿Cómo registra actualmente la empresa los reclamos oficiales de los usuarios y cómo entrega la constancia correspondiente?

## Lo que sabemos

- El módulo `libroreclamo` del código auditado está incompleto: referencia estructuras inexistentes y una operación faltante.
- La lectura del código no demuestra que ese módulo sea el canal legal vigente.
- D3 es independiente de `fleet`, `ticketing`, `cargo` y `billing`.

## Lo que no sabemos

- Si el canal vigente es el módulo SISGETRAN, una web externa, un portal de proveedor, un libro físico u otro software.
- Quién lo administra, dónde se conserva la constancia y cómo se atienden los plazos.

## Opciones a confirmar

| Canal | Evidencia solicitada, sin PII |
|---|---|
| Módulo SISGETRAN | URL/pantalla vigente y procedimiento operativo |
| Web externa | Responsable, proveedor y constancia de disponibilidad |
| Portal del proveedor | Contrato o procedimiento y responsable |
| Libro físico | Ubicación, custodia y procedimiento de registro |
| Software diferente | Nombre del sistema, responsable e integración si existe |
| Otro | Descripción y evidencia de cumplimiento |

## Clasificación

**NO DETERMINADO.** Si no existe un canal vigente o el único es el módulo roto, cambiar a `REQUIERE REEMPLAZO`. Si legal y operaciones aportan evidencia, cambiar a `CANAL CONFIRMADO`.

## Responsable y decisión final

- Responsable: Legal / Atención al Cliente / Operaciones.
- Decisión final: **PENDIENTE**.
