# ZKTeco ADMS/iClock

Ruta compatible: `GET|POST /iclock/cdata?SN=<serial>`.

- GET devuelve configuración básica de handshake.
- POST acepta líneas ATTLOG tabuladas, actualiza la última conexión y responde texto plano.
- Dispositivos desconocidos o inactivos reciben 403.
- Reenvíos no duplican eventos por la restricción dispositivo+PIN+fecha+método.
- El evento crudo queda disponible para auditoría y reprocesamiento.

Ejemplo: `1001\t2026-09-20 08:00:00\t0\t1`.
