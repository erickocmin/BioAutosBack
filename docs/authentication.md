# Autenticación

JWT de 15 minutos, refresh de 8 horas, rotación y blacklist. Las contraseñas se guardan con los hashers de Django y validadores de fortaleza. Endpoints: login, refresh, logout y `me`. El login tiene throttling y respuesta genérica.
