# D1 — seguridad de credenciales legacy

Fecha de revisión local: 20 de septiembre de 2026.

No se registran valores, hosts, usuarios, contraseñas ni tokens en este documento. La revisión identifica ubicaciones y responsables; la rotación debe verificarse en el sistema administrador de cada secreto.

## Inventario verificable

| Clase | Evidencia local | Riesgo | Estado | Evidencia necesaria para cerrar |
|---|---|---|---|---|
| PostgreSQL legacy, conexión principal | `lib/Spdo.php` contiene configuraciones versionadas | Acceso no autorizado a datos legacy | PENDIENTE | Fecha de rotación, identificador no secreto de credencial nueva y confirmación de revocación de todas las anteriores |
| PostgreSQL legacy, scripts directos | `update.php`, `ver.php` y `web/list_tpp.php` contienen conexiones fuera del punto central | Credencial duplicada y superficie HTTP adicional | PENDIENTE | Rotación/revocación y confirmación de que los scripts ya no aceptan la credencial antigua |
| API de facturación de tercero | `model/Main.php` contiene autenticación repetida para las funciones de envío | Uso fraudulento del proveedor y exposición de documentos | PENDIENTE | Confirmación del proveedor de emisión de credencial nueva y revocación de la anterior |
| API de consulta DNI/RUC | `lib/consulta_r.php` y `lib/consulta_s.php` contienen token versionado | Consumo indebido, coste y exposición de consultas | PENDIENTE | Confirmación del proveedor de rotación y revocación |

La búsqueda local por indicadores de secreto produjo falsos positivos en librerías vendorizadas y formularios de contraseña. No se clasificaron como credenciales sin evidencia concreta.

## Checklist administrativo

- [ ] Designar propietario técnico de cada secreto.
- [ ] Crear una credencial distinta por servicio y ambiente.
- [ ] Rotar sin reutilizar valores anteriores.
- [ ] Revocar explícitamente las credenciales antiguas.
- [ ] Revisar logs del proveedor desde la fecha de exposición.
- [ ] Retirar secretos del código desplegado y usar configuración segura.
- [ ] Confirmar que una prueba con la credencial anterior falla.
- [ ] Conservar solo fecha, responsable y comprobante no secreto de la rotación.
- [ ] Evaluar limpieza del historial Git; no asumir que borrar el archivo actual elimina la exposición histórica.

## Criterio de estados

- `ROTADA Y REVOCADA`: existe evidencia de emisión nueva y prueba de rechazo de la anterior.
- `ROTADA, REVOCACIÓN NO CONFIRMADA`: hay credencial nueva, pero no se probó el rechazo de la anterior.
- `PENDIENTE`: existe exposición confirmada y no se aportó evidencia de rotación.
- `NO VERIFICABLE`: el proveedor o sistema no permite obtener evidencia suficiente.

## Resultado D1

**PENDIENTE.** El inventario técnico está cerrado, pero no hay evidencia administrativa de rotación o revocación. D1 no bloquea el modelado de subdominios; sí es una remediación urgente del sistema productivo.
