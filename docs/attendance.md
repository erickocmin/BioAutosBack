# Asistencia

`AttendanceEvent` es la fuente inmutable; `DailyAttendance` es un agregado recalculable. El empleado se busca por `biometric_pin`. Se conservan PIN, timestamp, estado del dispositivo, método, confianza opcional y `raw_data`. No se almacenan imágenes, embeddings ni plantillas biométricas.

Procesar pendientes: `python manage.py process_attendance --limit 1000`.
