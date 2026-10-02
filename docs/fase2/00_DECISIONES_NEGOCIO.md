# Fase 2 — sesión de decisiones de negocio

Estado de análisis: 20 de septiembre de 2026.

Este documento prepara la sesión necesaria para desbloquear los dominios operativos de Fase 2. No sustituye una decisión del dueño del producto, del equipo operativo, de contabilidad ni de infraestructura. Las recomendaciones técnicas reducen riesgo, pero no cambian reglas comerciales por sí solas.

Fuentes de verdad consultadas:

- `sys_bio/docs/auditoria/`, especialmente reglas de negocio, seguridad y preguntas pendientes.
- `sys_bio/docs/migracion/`, especialmente fuentes de verdad, estados, correlativos, permisos, integraciones y apps definitivas.
- `sisgetran-backend/docs/validacion-fase-1.md` para confirmar el baseline funcional existente.

## Clasificación ejecutiva

| Decisión | Estado | Dominio afectado | Bloqueante |
|---|---|---|---|
| D1 | RESOLUBLE POR EVIDENCIA TÉCNICA | Seguridad transversal | No para el diseño; remediación urgente de producción |
| D2 | RESOLUBLE POR EVIDENCIA TÉCNICA | `billing` | Sí |
| D3 | REQUIERE NEGOCIO | `customers` / cumplimiento legal | No para los cuatro dominios, sí para Libro de Reclamaciones |
| D4 | RESOLUBLE POR EVIDENCIA TÉCNICA | Seguridad transversal | No para el diseño; verificación urgente de producción |
| D5 | REQUIERE NEGOCIO | `ticketing`, `treasury` | Sí |
| D6 | RESOLUCIÓN TÉCNICA PARCIAL; REQUIERE OPERACIÓN | `cargo`, partes de `fleet`, `billing` | Solo capacidades que consumen esas fuentes |
| D7 | RESOLUBLE POR EVIDENCIA TÉCNICA | Todos, especialmente `fleet` | Sí para confirmar modelos productivos |
| D8 | RESOLUCIÓN TÉCNICA PARCIAL; REQUIERE NEGOCIO | `billing` | `sunat-adapter`, CDR y flujo legal |
| D9 | REQUIERE NEGOCIO | `hr` | Sí para implementar esa regla |
| D10 | REQUIERE NEGOCIO | `hr`, reglas de deuda que afectan flota | Sí para implementar esa regla |
| D11 | REQUIERE NEGOCIO | `treasury`, `hr` | Sí para migrar créditos |
| D12 | REQUIERE NEGOCIO | `treasury` | Sí para migrar cheques |
| D13 | REQUIERE NEGOCIO | `fleet`, `hr` | Sí para migrar papeletas |
| D14 | REQUIERE NEGOCIO | `accounts` | No para iniciar `fleet` |
| D15 | REQUIERE NEGOCIO | `fleet` | Sí para la validación de deuda vehicular |
| D16 | REQUIERE NEGOCIO | `customers`, dependencia de `ticketing` y `cargo` | Sí antes de deduplicar o imponer unicidad |
| D17 | RESOLUCIÓN TÉCNICA PARCIAL; REQUIERE OPERACIÓN | `treasury`, `hr` | Solo `estadocta`/`presupuestos` |

Resumen actualizado: ninguna decisión está cerrada administrativamente; D6, D8 y D17 tienen resolución técnica parcial. D2, D4 y D7 conservan consultas/checklists pendientes de ejecución autorizada. El bloqueo se evalúa por subdominio en `13_MATRIZ_SUBDOMINIOS.md`.

## Matriz D1–D17

| ID | Dominio | Pregunta | Por qué importa | Opciones | Recomendación técnica | Decisión final |
|---|---|---|---|---|---|---|
| D1 | Seguridad transversal | ¿Se rotaron todas las credenciales de base de datos y APIs expuestas en el legacy? | Las credenciales aparecen versionadas y deben considerarse comprometidas. | Rotación completa; rotación parcial; mantenerlas. | Rotar todas, revocar las anteriores y verificar desde los proveedores sin copiar secretos a tickets, Git ni este documento. | **PENDIENTE.** Infraestructura y propietarios de cada API deben aportar confirmación de rotación, no los valores secretos. |
| D2 | `billing` | ¿Alguna serie SUNAT activa está cerca de `valormaximo`? | El legacy reinicia el correlativo sin persistir el cambio de serie, con riesgo de duplicidad legal. | Ninguna próxima al límite; una o más próximas; series ya agotadas. | Ejecutar consulta de solo lectura en producción, congelar cualquier serie riesgosa y corregir el legacy por vía de emergencia si corresponde. | **PENDIENTE.** Requiere inventario certificado de series y distancias al límite. |
| D3 | `customers` / legal | ¿Existe un canal alternativo válido para el Libro de Reclamaciones? | El módulo auditado está roto/incompleto y existe una obligación legal que no puede inferirse del código. | Canal externo vigente; reparar/reemplazar el módulo; servicio tercerizado; no existe canal. | Validación conjunta legal-operaciones; conservar evidencia del canal vigente antes de retirar o reemplazar el legacy. | **PENDIENTE.** Responsable: legal/atención al cliente. |
| D4 | Seguridad transversal | ¿El `DocumentRoot` productivo apunta únicamente a `web/`? | Si apunta a la raíz, puede exponer scripts, configuración y metadatos sensibles. | `web/`; raíz del proyecto; proxy/virtual host con otra ruta. | Inspeccionar configuración efectiva del servidor y probar por HTTP que raíz, `.git`, scripts de diagnóstico y configuración no sean accesibles. | **PENDIENTE.** Infraestructura debe aportar configuración efectiva y resultado de prueba. |
| D5 | `ticketing` / `treasury` | ¿Cómo debe relacionarse una venta con caja y arqueo? | La auditoría confirma que el legacy no crea automáticamente el movimiento de arqueo; automatizarlo cambia el control operativo. | A: movimiento automático; B: movimiento pendiente de conciliación; C: arqueo manual desacoplado. | Preferir B como base técnica por trazabilidad y doble control, pero no implementarla sin aprobación explícita; documentar pros/contras y responsables de conciliación. | **PENDIENTE.** Dueño de producto, caja y contabilidad deben elegir A, B o C. |
| D6 | `cargo`, `fleet`, `billing` | ¿Qué representa el código que depende de `reglasnegocio`, `logistica` y `caja`, y cuál es su fuente real vigente? | Esos esquemas no existen en el mirror y varios flujos serían inejecutables; no se sabe si son código de otro producto o si producción difiere. | Código abandonado; esquemas presentes solo en producción; otro sistema vigente; funcionalidad requerida que debe rediseñarse. | Identificar el proceso operativo actual y sus tablas/sistemas reales; no portar referencias rotas ni crear tablas por semejanza de nombres. | **PENDIENTE.** Requiere confirmación operativa y evidencia de producción. |
| D7 | Todos / `fleet` | ¿Cuál es el perfil real de producción para catálogos y relaciones truncados en el mirror? | Vehículos, propietarios, personal, sucursales y manifiestos tienen 0–1 filas; no permiten confirmar cardinalidades, nulabilidad ni alcance. | Perfilado de solo lectura en producción; exportación anonimizada certificada; mantener el mirror insuficiente. | Repetir los scripts de auditoría con cuenta read-only y producir conteos, nulos, duplicados, huérfanos y catálogos sin extraer PII innecesaria. | **PENDIENTE.** Es el gate principal de `fleet`. |
| D8 | `billing` | ¿Cómo se completa actualmente el envío del TXT a SUNAT/OSE? | El código auditado no contiene un flujo automático funcional y usa rutas/esquemas incoherentes en modo DEV. | Carga manual en portal; software externo; proveedor/OSE; tarea productiva no auditada. | Levantar el flujo real con contabilidad y evidencias de estados/CDR; diseñar luego un adaptador nuevo con `fake provider` y sandbox, nunca copiar la integración legacy. | **PENDIENTE.** Responsable: facturación/contabilidad e infraestructura. |
| D9 | `hr` | ¿Los préstamos y compromisos deben cobrar interés o permanecer en tasa cero? | Activar la fórmula existente cambiaría importes y política comercial. | Tasa cero; tasa fija; tasa configurable por producto/fecha; fórmula distinta. | Mantener cero hasta aprobación; si se activa, calcular y validar en backend con versionado de política y pruebas de redondeo. | **PENDIENTE.** Finanzas/negocio debe definir tasa, vigencia y redondeo. |
| D10 | `hr` / deuda vehicular | ¿Cuál es el período de gracia correcto? | El legacy usa 26, 29 y 30 días en funciones relacionadas, produciendo resultados diferentes. | 26 días; 29 días; 30 días; reglas distintas por caso. | No unificar por intuición; definir una regla nombrada y fechada, calculada en backend, con ejemplos de cruce de mes/año. | **PENDIENTE.** Negocio debe resolver cada caso de uso. |
| D11 | `treasury` / `hr` | ¿Qué significa `procesos.cabcreditos.estado`, distinto de `estareg`? | Mezclar ambos campos puede corromper el ciclo de vida o aprobar/cancelar créditos indebidamente. | Aprobación; estado técnico; campo vestigial; otro ciclo de vida. | Conservar valor legacy como dato de origen durante ETL, sin mapearlo a un enum funcional hasta confirmar semántica y transiciones. | **PENDIENTE.** Crédito/caja y desarrollador original deben definirlo. |
| D12 | `treasury` | ¿Por qué casi todos los cheques figuran como `ANULADO`? | Puede ser una etiqueta de catálogo incorrecta, un default operativo o anulaciones reales; cada opción exige una migración distinta. | Anulados reales; catálogo mal etiquetado; campo no operativo; otra fuente de estado. | Muestrear expedientes y cruzar con contabilidad; no transformar ni descartar registros basándose solo en `estado=2`. | **PENDIENTE.** Contabilidad debe validar una muestra representativa. |
| D13 | `fleet` / `hr` | ¿Qué significan y cómo transicionan `papeleta.estado` y `estadopago`? | Hay 15 combinaciones reales y dos ciclos de vida; colapsarlos perdería información. | Dos estados independientes; estado compuesto; uno vestigial; catálogo externo. | Modelar provisionalmente dos dimensiones separadas, pero no fijar choices ni transiciones hasta obtener catálogo y casos operativos aprobados. | **PENDIENTE.** Operaciones/administración debe definir ambos ciclos. |
| D14 | `accounts` | ¿Se conserva el concepto de múltiples sistemas por usuario? | El mirror solo tiene un sistema; mantenerlo agrega complejidad, eliminarlo podría perder una capacidad productiva. | Conservar multi-sistema; un sistema implícito; preparar extensión futura sin exponerla ahora. | Confirmar producción y uso operativo; si solo existe uno, omitir la entidad `Sistema` y conservar perfiles/permisos multiempresa ya implementados. | **PENDIENTE.** Dueño de producto y administración de usuarios. |
| D15 | `fleet` | ¿Sigue vigente la exención de deuda del vehículo legacy 114? | Es una excepción comercial hardcodeada sin motivo ni vigencia; copiarla por ID sería inseguro. | Vigente; eliminada; temporal; aplicable a una categoría, no a un vehículo. | Nunca codificar el ID 114. Si se aprueba, crear una exención explícita con motivo, vigencia, autorización y `AuditLog`. | **PENDIENTE.** Gerencia/finanzas debe aportar fundamento y vigencia. |
| D16 | `customers` | ¿Cómo tratar DNI ausente o repetido entre clientes? | 35.5% no tiene DNI y existen documentos repetidos; `unique=True` rompería la carga o fusionaría personas incorrectamente. | Aceptar duplicados; limpieza previa; unicidad condicional; flujo de fusión; separar DNI/RUC y representante. | No imponer unicidad global todavía; perfilar con acceso autorizado, normalizar tipo+número y definir conciliación/fusión auditada. | **PENDIENTE.** Negocio y protección de datos deben aprobar identidad y deduplicación. |
| D17 | `treasury` / `hr` | ¿Qué proceso alimenta `estadocta` y `presupuestos`? | No se encontró escritor en el código; migrar tablas sin conocer su productor puede duplicar o perder el proceso real. | Batch; otro sistema; carga manual directa; datos históricos sin proceso vigente. | Revisar jobs, logs, usuarios escritores y operación real; bloquear el ETL de estas tablas hasta identificar propietario y frecuencia. | **PENDIENTE.** Infraestructura y áreas usuarias deben confirmarlo. |

## Pros y contras de D5: venta y caja

| Modelo | Ventajas | Riesgos / costes |
|---|---|---|
| A. Venta genera movimiento automático | Saldo en tiempo real; conciliación simple; menos captura manual. | Puede eliminar un control antifraude; exige resolver anulaciones, reprogramaciones, pagos mixtos y fallos parciales en la misma transacción. |
| B. Venta genera movimiento pendiente de conciliación | Trazabilidad por venta; conserva doble control; permite detectar diferencias. | Añade cola y estados de conciliación; requiere responsables, tiempos límite y resolución de discrepancias. |
| C. Arqueo manual | Conserva el proceso actual y su independencia; implementación inicial menor. | Menor trazabilidad dinero↔venta; más captura; conciliación y detección de errores siguen siendo manuales. |

## Semáforo inicial de dominios

Esta tabla histórica motivó la descomposición posterior. No debe usarse para bloquear automáticamente todas las capacidades de un dominio; la fuente vigente es `13_MATRIZ_SUBDOMINIOS.md`.

| Dominio | Estado | Puede empezar | Condiciones mínimas para cambiar a verde |
|---|---|---|---|
| `fleet` | 🔴 BLOQUEADO | No | Cerrar D7 con perfilado productivo; aclarar la fuente de D6; resolver D15 antes de implementar deuda; obtener catálogos/transiciones de D13 si las papeletas entran en alcance. |
| `ticketing` | 🔴 BLOQUEADO | No | Resolver D5; confirmar fuente real de ventas/viajes/asientos y sus estados; disponer de `fleet` y estrategia de identidad de D16. |
| `cargo` | 🔴 BLOQUEADO | No | Resolver D6; confirmar tablas y flujo realmente operativos; definir comisión/estados/pagos con negocio y estrategia de clientes. |
| `billing` | 🔴 BLOQUEADO | No | Resolver D2 y D8; confirmar fuentes de D6; aprobar series/correlativos y flujo SUNAT/OSE; disponer del dominio emisor correspondiente. |

## Evidencia que desbloquea el siguiente paso

1. Un perfilado read-only de producción para D2 y D7, ejecutado por una persona autorizada y sin copiar PII al repositorio.
2. La configuración efectiva de Apache/proxy y prueba de exposición para D4.
3. Acta de sesión con responsables y decisiones explícitas para D5, D6, D8 y D15.
4. Catálogos y ejemplos anonimizados para estados de papeletas, créditos y cheques.
5. Descripción operativa verificable del proceso SUNAT/OSE y de los procesos externos de D17.

Mientras esta tarea de evidencia esté abierta, no se deben crear `apps/fleet`, `apps/ticketing`, `apps/cargo` ni `apps/billing`, ni sus equivalentes frontend. El próximo incremento podrá limitarse al primer subdominio que cumpla los criterios de verde, sin arrastrar reglas rojas no relacionadas.
