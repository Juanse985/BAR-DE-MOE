# Evidencia · frontend por perfiles (HU-009, HU-010, HU-011, RNF-01)

Revisión automática en Chromium (Playwright) contra la plataforma integrada. Capturas en `capturas/`.

| Perfil | Verificación | Resultado |
|---|---|---|
| ADMINISTRADOR | menú: Sedes, Mesas, Tipos de producto, Proveedores, Productos, Usuarios | ✅ |
| ADMINISTRADOR | tipos de producto visibles | ✅ |
| ADMINISTRADOR | crear sede por pantalla | ✅ |
| ADMINISTRADOR | error de duplicado visible | ✅ |
| ADMINISTRADOR | desbloquear desde pantalla | ✅ |
| ADMINISTRADOR | inactivar / activar | ✅ |
| MESERO | menú: Mesas, Pedidos | ✅ |
| MESERO | solo mesas de su sede | ✅ |
| MESERO | ruta no permitida vuelve al inicio | ✅ |
| CAJERO | menú: Pedidos, Facturacion, Consulta de facturas, Reporte de ventas | ✅ |
| - | login fallido genérico | ✅ |
| - | login sin scroll horizontal en celular | ✅ |

El único error de consola es el 409 esperado al intentar crear una sede duplicada.
