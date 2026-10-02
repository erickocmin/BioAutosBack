# Guía de reuniones de negocio — Fase 2A

Usar lenguaje operativo y registrar ejemplos sin datos personales. Cada decisión debe quedar con responsable, fecha, alcance y decisión final explícita.

## Apertura: comprobaciones técnicas

- D1: ¿Seguridad confirma que todas las credenciales expuestas fueron rotadas y las antiguas revocadas?
- D2: Facturación debe revisar el reporte de series ejecutado por infraestructura.
- D4: Infraestructura debe presentar la configuración efectiva y prueba de rutas sensibles.
- D7: Infraestructura/datos debe presentar únicamente agregados del perfil productivo.

## Sesión 1 — bloqueantes operativos

### D5 — venta y caja

**Pregunta:** ¿El nuevo sistema debe registrar automáticamente el dinero de una venta, dejarlo pendiente de conciliación o conservar el arqueo manual?

**Sabemos:** el legacy no conecta automáticamente venta y arqueo.
**No sabemos:** si esa separación es un control intencional.
**A:** automático; más rapidez, mayor complejidad en reversos.
**B:** conciliación; mejor trazabilidad y doble control, más estados.
**C:** manual; conserva operación, menor trazabilidad.
**Recomendación técnica:** B, sujeta a aprobación.
**Responsable:** Caja, Operaciones, Contabilidad y Producto.
**Decisión final:** ____________________

### D6 — fuentes ausentes

**Pregunta:** ¿Qué sistema usa hoy la empresa para guías, carga, líneas y datos que el código busca en esquemas inexistentes?
**Sabemos:** esos esquemas no existen en el mirror y no hay conexión alternativa en el repositorio.
**No sabemos:** si existen solo en producción, en otro sistema o son código abandonado.
**A:** fuente productiva separada; identificar propietario e interfaz.
**B:** código abandonado; no migrarlo.
**C:** función necesaria pero rota; rediseñarla con reglas aprobadas.
**Recomendación técnica:** demostrar la fuente operativa antes de modelar.
**Responsable:** Operaciones, Infraestructura y proveedor original.
**Decisión final:** ____________________

### D8 — SUNAT/OSE

**Pregunta:** ¿Quién toma hoy el TXT, dónde lo carga, cómo recibe la respuesta y dónde guarda el CDR?
**Sabemos:** SISGETRAN genera TXT; no tiene un envío automático completo verificable.
**No sabemos:** el sistema externo y el manejo de rechazos/CDR.
**A:** portal manual.
**B:** software externo de escritorio.
**C:** proveedor/OSE integrado fuera de SISGETRAN.
**Recomendación técnica:** reconstruir el recorrido real y luego diseñar un adaptador nuevo.
**Responsable:** Facturación, Contabilidad e Infraestructura.
**Decisión final:** ____________________

### D13 — papeletas

**Pregunta:** ¿Qué significa cada estado de la papeleta y cada estado de pago, y quién puede cambiarlos?
**Sabemos:** hay dos dimensiones y 15 combinaciones reales.
**No sabemos:** significado y transiciones.
**Opciones:** dos ciclos separados; ciclo compuesto; campo legacy.
**Recomendación técnica:** mantenerlos separados hasta demostrar lo contrario.
**Responsable:** Operaciones/Administración.
**Decisión final:** ____________________

### D15 — excepciones de deuda

**Pregunta:** ¿Existe una política vigente de excepciones al bloqueo de vehículos por deuda?
**Sabemos:** existe una excepción hardcodeada sin explicación.
**No sabemos:** motivo, vigencia y autoridad.
**A:** no hay excepciones.
**B:** autorización temporal auditada.
**C:** regla por categoría/convenio.
**Recomendación técnica:** nunca basarla en un ID; exigir vigencia y auditoría.
**Responsable:** Gerencia, Finanzas y Operaciones.
**Decisión final:** ____________________

### D16 — identidad de clientes

**Pregunta:** ¿Cuándo dos registros con el mismo documento representan a la misma persona/empresa y quién autoriza fusionarlos?
**Sabemos:** hay documentos vacíos y repetidos.
**No sabemos:** causas y política de identidad.
**A:** aceptar duplicados controlados.
**B:** limpieza previa.
**C:** merge auditado.
**Recomendación técnica:** tipo+número normalizados y fusión humana auditada.
**Responsable:** Operaciones, Atención al Cliente y Protección de Datos.
**Decisión final:** ____________________

## Sesión 2 — Finanzas y RRHH

### D9

**Pregunta:** ¿Los préstamos deben seguir sin interés o usar una tasa aprobada?
**Sabemos:** hoy la tasa efectiva es cero. **No sabemos:** si es política o desactivación temporal.
**Opciones:** cero; tasa fija; tasa configurable.
**Recomendación:** mantener cero hasta aprobación y calcular en backend.
**Responsable:** Finanzas/RRHH. **Decisión:** __________

### D10

**Pregunta:** ¿Cuál es la gracia correcta para deuda mensual y cambia por escenario?
**Sabemos:** el código usa 26, 29 y 30 días. **No sabemos:** cuál regla está vigente.
**Opciones:** una cifra común; reglas distintas documentadas.
**Recomendación:** aprobar ejemplos de cruce de mes/año.
**Responsable:** Finanzas. **Decisión:** __________

### D11

**Pregunta:** ¿Qué representa el segundo `estado` del crédito?
**Sabemos:** es distinto de `estareg`. **No sabemos:** si es aprobación, estado técnico o vestigial.
**Opciones:** ciclo separado; campo legacy; otro catálogo.
**Recomendación:** conservar valor bruto hasta definirlo.
**Responsable:** Créditos/Finanzas. **Decisión:** __________

### D12

**Pregunta:** ¿Por qué casi todos los cheques aparecen anulados?
**Sabemos:** `estado=2` domina el mirror. **No sabemos:** si la etiqueta o el proceso son correctos.
**Opciones:** anulaciones reales; catálogo erróneo; campo no operativo.
**Recomendación:** validar una muestra contable.
**Responsable:** Contabilidad. **Decisión:** __________

### D17

**Pregunta:** ¿Quién mantiene `presupuestos` y sigue vigente `regfactura` para estado de cuenta?
**Sabemos:** `regfactura` escribe `estadocta`; el módulo “presupuestos” escribe otra tabla.
**No sabemos:** origen real de `administrativo.presupuestos` y uso productivo.
**Opciones:** carga manual; batch; otro sistema; histórico.
**Recomendación:** confirmar con logs/operación antes de ETL.
**Responsable:** Contabilidad e Infraestructura. **Decisión:** __________

## Sesión 3 — Administración y Legal

### D3

**Pregunta:** ¿Cuál es el canal oficial actual del Libro de Reclamaciones?
**Sabemos:** el módulo auditado está incompleto.
**Opciones:** web, portal, físico, otro software, reemplazo.
**Recomendación:** conservar evidencia legal del canal.
**Responsable:** Legal/Atención al Cliente. **Decisión:** __________

### D14

**Pregunta:** ¿Una persona necesita perfiles diferentes en más de un sistema?
**Sabemos:** el mirror solo demuestra un sistema; multiempresa sí es real.
**Opciones:** conservar multi-sistema; sistema único; extensión futura.
**Recomendación:** simplificar solo con confirmación productiva.
**Responsable:** Administración de usuarios/Producto. **Decisión:** __________

## Cierre de cada sesión

- Confirmar responsable y fecha de vigencia.
- Registrar ejemplos y excepciones sin PII.
- Identificar quién aprueba cambios futuros.
- No aceptar “como funciona ahora” sin describir el proceso observable.
