# D15 — política de excepciones al bloqueo por deuda

## Pregunta

> ¿Existe una política vigente que permita autorizar temporalmente a determinados vehículos pese a un bloqueo por deuda?

La pregunta no se formula alrededor del ID legacy 114: ese número es una implementación accidental, no una política.

## Lo que sabemos

- El legacy excluye de una validación concreta al vehículo `idvehiculo=114` mediante código hardcodeado.
- No existe comentario, vigencia, responsable ni motivo estructurado.
- La regla de deuda combina documentos, mensualidades, papeletas y varios tipos de crédito.

## Lo que no sabemos

- Si la excepción sigue vigente.
- Si corresponde a un vehículo, empresa, contrato, categoría o contingencia.
- Quién puede autorizarla y revocarla.

## Opciones

### A. No existen excepciones

Todo bloqueo vigente impide operar. El caso 114 se trata como deuda técnica del legacy y no se migra.

### B. Excepción temporal autorizada

Debe registrar motivo, alcance, responsable, fecha de inicio, fecha de fin, autorización, revocación y auditoría.

### C. Política por categoría

La excepción depende de una regla aprobada —por ejemplo un convenio— y no de un ID individual. Debe ser explícita, versionada y auditable.

## Recomendación técnica

No implementar nunca `if vehicle.id == 114`. Si negocio aprueba excepciones, modelarlas como autorizaciones independientes, de vigencia limitada, con permisos especiales y `AuditLog`.

## Responsable y decisión final

- Responsable: Gerencia, Finanzas y Operaciones.
- Decisión: **PENDIENTE**.
- Bloqueo exacto: `fleet.debt-validation`; no bloquea `fleet.catalogs` ni `fleet.routes`.
