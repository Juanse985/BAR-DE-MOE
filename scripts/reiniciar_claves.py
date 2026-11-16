"""Reinicia las contraseñas de los usuarios a las de la demo (solo para desarrollo y pruebas).

Se corre DENTRO del contenedor de auth-service, que ya tiene la conexión a la base:

    docker cp scripts/reiniciar_claves.py barmoe-auth:/tmp/reiniciar_claves.py
    docker exec barmoe-auth python /tmp/reiniciar_claves.py

Para cada usuario:
  · pone la contraseña de la demo (los usuarios de seed.py la suya; cualquier otro, la de su perfil);
  · lo desbloquea y pone en cero los intentos fallidos;
  · quita la obligación de cambiar la contraseña;
  · cierra sus sesiones abiertas (así no choca con la sesión única al volver a entrar).

Opcional: `python /tmp/reiniciar_claves.py omann pbouvier` reinicia solo esos usuarios.
"""
import os
import sys
from datetime import UTC, datetime

from sqlalchemy import create_engine, text

from barmoe_common.security import hashear_password

POR_USUARIO = {
    "admin": "Admin2026",
    "mszyslak": "Cerveza2026",
    "ccarlson": "Cajero2026", "lleonard": "Cajero2026", "pbouvier": "Cajero2026",
    "bgumble": "Mesero2026", "sgumble": "Mesero2026", "omann": "Mesero2026",
}
POR_PERFIL = {"ADMINISTRADOR": "Admin2026", "CAJERO": "Cajero2026", "MESERO": "Mesero2026"}


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("✗ No encuentro DATABASE_URL. Córrelo dentro del contenedor (docker exec barmoe-auth ...).")
        return 1
    solo = {u.lower() for u in sys.argv[1:]}
    motor = create_engine(url)
    ahora = datetime.now(UTC)
    filas = []
    with motor.begin() as cx:
        usuarios = cx.execute(text("SELECT id, usuario, perfil FROM usuarios ORDER BY perfil, usuario")).all()
        for uid, usuario, perfil in usuarios:
            if solo and usuario.lower() not in solo:
                continue
            clave = POR_USUARIO.get(usuario, POR_PERFIL.get(perfil, "Bar2026Moe"))
            cx.execute(text("UPDATE usuarios SET password_hash = :h, intentos_fallidos = 0, bloqueado = :f, "
                            "bloqueado_hasta = NULL, debe_cambiar_password = :f, estado = 'ACTIVO' "
                            "WHERE id = :id"),
                       {"h": hashear_password(clave), "f": False, "id": uid})
            cerradas = cx.execute(text("UPDATE sesiones SET activa = :f, cerrada_en = :t, "
                                       "motivo_cierre = 'REINICIO' WHERE usuario_id = :id AND activa = :v"),
                                  {"f": False, "v": True, "t": ahora, "id": uid}).rowcount
            filas.append((usuario, perfil, clave, cerradas))
    if not filas:
        print("✗ No se encontró ningún usuario con esos nombres.")
        return 1
    print(f"\n{'Usuario':<14}{'Perfil':<16}{'Contraseña':<14}Sesiones cerradas")
    print("-" * 60)
    for usuario, perfil, clave, cerradas in filas:
        print(f"{usuario:<14}{perfil:<16}{clave:<14}{cerradas}")
    print(f"\n✔ {len(filas)} usuario(s) reiniciado(s): desbloqueados y sin cambio de contraseña pendiente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
