# ZKTeco ADMS/iClock local

La integración usa el modo push ADMS del terminal. El equipo reconoce la huella y envía solamente el PIN, la hora, el estado de entrada/salida y el método de verificación. SISGETRAN no almacena imágenes ni plantillas biométricas.

## Puesta en marcha local

1. Conectar el huellero y la PC a la misma red Ethernet.
2. Ejecutar Django accesible por la LAN: `python manage.py runserver 0.0.0.0:8000`.
3. Permitir TCP 8000 en el firewall únicamente para redes privadas.
4. Abrir `/attendance/biometric` en el frontend y autorizar la serie del equipo (por defecto `CMYD231760447`).
5. En el terminal abrir `COMM > Cloud Server` o `ADMS`, indicar la IP LAN de la PC, puerto `8000` y desactivar HTTPS para esta instalación local.
6. Registrar la cuenta/empleado en la misma pantalla. El PIN biométrico debe coincidir con el ID del usuario en el terminal.
7. Enrolar físicamente el dedo en el huellero usando ese PIN.

No se debe configurar `localhost` en el huellero: allí `localhost` sería el propio terminal. Debe usarse la IP privada de la PC, por ejemplo `192.168.1.20`.

## Rutas de dispositivo

- `GET|POST /iclock/cdata?SN=<serial>`: handshake y recepción de `ATTLOG`.
- `GET /iclock/getrequest?SN=<serial>` y variante `.aspx`: heartbeat y entrega de comandos.
- `POST /iclock/devicecmd?SN=<serial>`: confirmación de comandos.

- GET devuelve configuración básica de handshake.
- POST acepta líneas ATTLOG tabuladas, actualiza la última conexión y responde texto plano.
- Dispositivos desconocidos o inactivos reciben 403.
- Reenvíos no duplican eventos por la restricción dispositivo+PIN+fecha+método.
- El evento crudo queda disponible para auditoría y reprocesamiento.
- Por defecto solo se aceptan conexiones desde IP privadas o loopback. `ATTENDANCE_ALLOW_PUBLIC_DEVICE_IPS=true` debe usarse únicamente detrás de controles de red adicionales.
- El alta desde la pantalla crea usuario y empleado en una sola transacción y puede encolar `USERINFO`; la huella se enrola físicamente en el equipo.

Ejemplo: `1001\t2026-09-20 08:00:00\t0\t1`.

Estados comunes: `0` entrada, `1` salida, `2` salida a descanso, `3` retorno, `4` entrada extra y `5` salida extra. Firmwares que siempre envían `0` quedan como entrada; el resumen diario conserva primera y última marcación como respaldo.
