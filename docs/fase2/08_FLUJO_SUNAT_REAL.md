# D8 — flujo SUNAT/OSE real

## Pregunta

> Desde que se genera un comprobante hasta que se obtiene su aceptación o rechazo, ¿qué personas y sistemas intervienen hoy?

## Lo que sabemos por código

1. El flujo normal guarda el documento en la base legacy.
2. Imprime un ticket/PDF con QR, pero no obtiene un hash SUNAT verificable en ese flujo.
3. El módulo `factelectronica` puede generar manualmente un TXT por rango de fechas.
4. No se encontró código que suba automáticamente ese TXT.
5. El único intento de API usa esquemas/tablas incompatibles con el mirror y está configurado en modo DEV.
6. Los botones de envío y la consulta de estado no forman un circuito backend completo.

## Lo que no sabemos

- Quién toma el TXT.
- En qué portal o software se carga.
- Si el receptor es SUNAT directamente o un OSE/PSE.
- Dónde queda el CDR y cómo se vincula al documento original.
- Cómo se notifican, corrigen y reintentan rechazos.
- Si existe otro sistema productivo ausente del repositorio auditado.

## Guion de reconstrucción

| Paso | Pregunta operativa | Evidencia no sensible solicitada |
|---|---|---|
| Documento | ¿Qué documento inicia el proceso y quién lo emite? | Tipo, estado y responsable; sin datos del cliente |
| Archivo | ¿Qué archivo produce SISGETRAN y con qué frecuencia? | Formato, volumen agregado y procedimiento |
| Transferencia | ¿Quién recoge el archivo y cómo lo traslada? | Rol y sistema; no credenciales |
| Receptor | ¿Se usa SUNAT, OSE, PSE o portal de proveedor? | Nombre contractual del servicio |
| Respuesta | ¿Cómo llega aceptación/rechazo? | Estados posibles y tiempo esperado |
| CDR | ¿Dónde se almacena y cómo se consulta? | Repositorio y política de retención |
| Rechazo | ¿Quién corrige, reenvía y autoriza? | Flujo y responsables |
| Contingencia | ¿Qué ocurre cuando el servicio no está disponible? | Procedimiento aprobado |

## Recomendación técnica

Separar documento interno, comprobante electrónico, intento de envío, respuesta y CDR. Implementar primero con proveedor falso y sandbox; el adaptador real solo después de confirmar el proceso y contrato vigente.

## Responsable

Facturación, Contabilidad e Infraestructura; incluir al proveedor/OSE cuando corresponda.

## Resultado D8

**PARCIALMENTE RESUELTA.** El flujo dentro del código está reconstruido; el tramo operativo externo sigue `NO DETERMINADO`. Bloquea `billing.sunat-adapter`, `billing.cdr` y cierres tributarios relacionados.
