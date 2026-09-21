# Matriz de subdominios de Fase 2A

## Criterio

- 🟢 `LISTO`: modelo, fuente, reglas, estados y dependencias confirmados; sin decisión crítica pendiente.
- 🟡 `PARCIAL`: existe evidencia útil y el diseño puede profundizarse, pero falta validación productiva o una fuente inequívoca.
- 🔴 `BLOQUEADO`: falta una decisión funcional crítica o no existe una fuente de verdad utilizable.

Una decisión D9–D17 solo afecta las filas que la consumen.

## Fleet

| Subdominio | Depende de | Decisión | Evidencia | Estado |
|---|---|---|---|---|
| `fleet.catalogs` | clase, color, marca, modelo, estados | D6, D7 | Estructuras parciales; controladores de catálogo apuntan también a tablas inexistentes y `modelo` aparece embebido como texto en vehículo | 🟡 PARCIAL |
| `fleet.vehicles` | propietarios, catálogos, sucursal | D7 | `public.vehiculo` y campos documentados, pero 0 filas en mirror; sucursal operativa y modelo relacional no confirmados | 🟡 PARCIAL |
| `fleet.owners` | identidad/ubigeo | D7 | `public.propietario` documentada, 0 filas en mirror | 🟡 PARCIAL |
| `fleet.drivers` | personal/transportista | D7 | `public.transportista` y otras referencias a conductor; entidad funcional real no confirmada | 🟡 PARCIAL |
| `fleet.documents` | vehículo/conductor | D7 | Fechas SOAT, revisión, permisos y licencia visibles; fuentes auxiliares referenciadas por alertas están rotas/ausentes | 🟡 PARCIAL |
| `fleet.routes` | sucursal/origen/destino | D7 | `public.recorridos` documentada, pero 0 filas productivamente representativas | 🟡 PARCIAL |
| `fleet.lines` | rutas/vehículos | D6, D7 | Coexisten `public.vehiculo.idlinea`, `comercial.linea` y referencias legacy; fuente final no confirmada | 🟡 PARCIAL |
| `fleet.manifests` | vehículo, ruta, conductor, series | D2, D7 | `transportes.manifiesto` documentada, 0 filas; usa correlativos documentales | 🟡 PARCIAL |
| `fleet.papeletas` | vehículo, infractor | D7, D13 | 7,259 filas y matriz de estados disponible; semántica/transiciones desconocidas | 🔴 BLOQUEADO |
| `fleet.debt-validation` | documentos, papeletas, mensualidades, créditos | D10, D13, D15 | Doce motivos reconstruidos; gracia contradictoria y excepción hardcodeada sin política | 🔴 BLOQUEADO |

## Ticketing

| Subdominio | Depende de | Decisión | Evidencia | Estado |
|---|---|---|---|---|
| `ticketing.trips` | rutas, vehículo, conductor, salida | D7 | Tablas centrales de salidas sin volumen representativo y fleet no validado | 🔴 BLOQUEADO |
| `ticketing.seats` | vehículo/plantilla/viaje | D7 | Estructuras de asientos/plantillas conocidas, sin operación productiva confirmada | 🔴 BLOQUEADO |
| `ticketing.sales` | viaje, asiento, cliente, tarifa | D5, D7, D16 | Workflow reconstruido, pero fuente real de venta y relación económica no confirmadas | 🔴 BLOQUEADO |
| `ticketing.passengers` | identidad de cliente/persona | D16 | Alto volumen de clientes, DNI incompleto/repetido y distinción cliente/pasajero pendiente | 🔴 BLOQUEADO |
| `ticketing.fares` | ruta, origen/destino, tipo pasajero | D7 + reglas específicas de negocio | Lógica dispersa y catálogos productivos no confirmados | 🔴 BLOQUEADO |
| `ticketing.reservations` | viaje/asiento/estados | Reglas específicas de ticketing | Estados y vigencia de reserva no aprobados | 🔴 BLOQUEADO |
| `ticketing.cancellations` | venta/documento/caja | D5, D8 | Trazabilidad requerida; efectos económicos y tributarios pendientes | 🔴 BLOQUEADO |
| `ticketing.rescheduling` | venta original/nuevo viaje/tarifa | D5, D7 | Flujo legacy parcial; reglas económicas y fuentes no confirmadas | 🔴 BLOQUEADO |
| `ticketing.treasury-link` | venta y arqueo | D5 | Ausencia de vínculo automático confirmada; modelo futuro pendiente de negocio | 🔴 BLOQUEADO |

## Cargo

| Subdominio | Depende de | Decisión | Evidencia | Estado |
|---|---|---|---|---|
| `cargo.customers` | identidad de remitente/destinatario | D16 | Fuente cliente con calidad documental pendiente | 🔴 BLOQUEADO |
| `cargo.shipments` | cliente, origen/destino, estados | D6, D7 | Código mezcla fuentes existentes con `reglasnegocio.*`; tabla operativa real no confirmada | 🔴 BLOQUEADO |
| `cargo.reception` | envío/ubicación/usuario | D6 | Varias rutas dependen de esquemas ausentes; flujo real pendiente | 🔴 BLOQUEADO |
| `cargo.delivery` | recepción, cobro, identidad | D6, D16 | “Cobrar = entregar” requiere confirmación funcional y fuente real | 🔴 BLOQUEADO |
| `cargo.guides` | envío, series, vehículo | D2, D6 | `reglasnegocio.guia/dtguia` ausentes; correlativos productivos desconocidos | 🔴 BLOQUEADO |
| `cargo.payments` | caja/conciliación | D5, D6 | Múltiples flujos clonados y tablas incoherentes | 🔴 BLOQUEADO |
| `cargo.telegiro` | cliente, tarifa/comisión, caja | D6, D16 + regla de comisión | Comisión desactivada y fuente operativa no confirmada | 🔴 BLOQUEADO |

## Billing

| Subdominio | Depende de | Decisión | Evidencia | Estado |
|---|---|---|---|---|
| `billing.document-types` | catálogo documental | D7 | Estructura de `public.tipodocumento` confirmada, pero 0 filas en mirror | 🟡 PARCIAL |
| `billing.series` | empresa/sucursal/tipo | D2 | Estructura conocida, 0 filas y riesgo actual no medible | 🔴 BLOQUEADO |
| `billing.correlatives` | serie y bloqueo transaccional | D2 | Bug legacy confirmado; datos y rollover productivos pendientes | 🔴 BLOQUEADO |
| `billing.documents` | operación emisora/cliente/serie | D5, D6, D8, D16 | Persistencia interna parcial; proceso legal completo no confirmado | 🔴 BLOQUEADO |
| `billing.sunat-adapter` | proveedor/OSE, documento | D8 | Integración legacy no operativa; sistema externo desconocido | 🔴 BLOQUEADO |
| `billing.cdr` | adaptador/respuesta | D8 | No se conoce recepción ni almacenamiento actual del CDR | 🔴 BLOQUEADO |
| `billing.cancellations` | documento, nota, proveedor | D8 | Notas y bajas no tienen flujo productivo confiable identificado | 🔴 BLOQUEADO |

## D9–D17: alcance exacto

| Decisión | Funcionalidad que bloquea | No bloquea |
|---|---|---|
| D9 | `hr.loans`, `hr.payment-commitments` en cálculo de interés | fleet, attendance, inventory |
| D10 | `hr.monthly-debt` y por dependencia `fleet.debt-validation` | vehículos, propietarios, rutas |
| D11 | `hr/treasury.credits` y su ETL de estados | caja/arqueo core ya validado |
| D12 | `treasury.cheques` y migración de su estado | caja/arqueo core |
| D13 | `fleet.papeletas` y parte de `fleet.debt-validation` | vehículos, rutas, documentos |
| D14 | capacidad multi-sistema de `accounts` | perfiles/permisos multiempresa existentes y fleet |
| D15 | `fleet.debt-validation` y autorizaciones de excepción | catálogos, vehículos, rutas |
| D16 | identidad/deduplicación de customers, pasajeros y actores de cargo | fleet core salvo vínculos personales específicos |
| D17 | ETL y ownership de `treasury.estadocta/presupuestos` | arqueo core y demás dominios |

## Primer candidato

`fleet-core` —catálogos, vehículos, propietarios, conductores, documentos, rutas y líneas— es el primer candidato natural, pero **todavía no está listo para implementar**. Para pasar a verde necesita como mínimo ejecutar D7 en producción y cerrar las ambigüedades de fuente D6 que afectan catálogos/líneas. D13 y D15 no deben incluirse en ese primer incremento.
