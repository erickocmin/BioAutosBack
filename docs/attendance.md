# Asistencia

`AttendanceEvent` es la fuente inmutable; `DailyAttendance` es un agregado recalculable. El empleado se busca por `biometric_pin`. Se conservan PIN, timestamp, dirección de entrada/salida, estado del dispositivo, método, confianza opcional y `raw_data`. No se almacenan imágenes, embeddings ni plantillas biométricas.

Los eventos recibidos por ADMS se procesan inmediatamente. Para recuperar pendientes: `python manage.py process_attendance --limit 1000`.

Alta local conjunta: `POST /api/v1/attendance/enrollments/`. Crea la cuenta de acceso y el empleado de forma atómica, asigna opcionalmente perfil y huellero, y encola el alta del PIN en el terminal. La plantilla de huella nunca viaja por esta API.
