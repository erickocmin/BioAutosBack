# Permisos

`Perfil → Permiso → Módulo` se evalúa en cada endpoint mediante `HasModulePermission`. Las acciones incluyen ver, crear, editar, eliminar, aprobar, anular, cerrar y exportar. Los querysets operativos se limitan además al ámbito empresa/sucursal de `UsuarioPerfil`; los intentos de escritura fuera de ámbito reciben 403 y los objetos ajenos no son enumerables (404). `PermissionGate` del frontend solo mejora UX; nunca sustituye estas barreras.
