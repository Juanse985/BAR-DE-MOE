# Convenciones de trabajo

## Ramas

```
main        ← solo releases. Nadie hace push directo.
└─ develop  ← integración. Todo llega por Pull Request.
   ├─ feat/auth-usuarios          (Angel)
   ├─ feat/infra-gateway          (Felipe)
   ├─ feat/parametrizacion        (David)
   └─ feat/calidad-trazabilidad   (Juan)
```

Ramas adicionales: `fix/<algo>` para correcciones, `docs/<algo>` para documentación.

## Commits

Formato *Conventional Commits*, en español:

```
feat(auth): agregar paginación al listado de usuarios
fix(gateway): propagar el request id en las respuestas de error
test(parametrizacion): cubrir el filtro de productos por sede
docs(arquitectura): registrar la decisión de sesión única
chore(infra): actualizar la imagen de postgres a 16.2
```

Ámbitos válidos: `auth`, `parametrizacion`, `gateway`, `common`, `infra`, `docs`, `tests`.

## Pull Requests

1. Antes de abrirlo: `git pull --rebase origin develop` y `pytest` verde.
2. Título con el mismo formato de los commits.
3. En la descripción: qué hace, cómo probarlo y a qué requisito del tablero responde.
4. **Una revisión aprobada** de otro integrante como mínimo.
5. CI en verde.
6. Merge con *squash* para que `develop` quede con un commit por PR.

Nadie aprueba su propio PR. Nadie mergea con el CI en rojo.

## El día a día

```bash
git checkout develop
git pull origin develop
git checkout feat/mi-rama
git rebase develop          # antes de empezar el día
# ... trabajar ...
pytest                      # antes de cada commit
git push origin feat/mi-rama
```

## Ceremonias

| Cuándo | Qué | Cuánto |
|---|---|---|
| Diario | Daily Scrum | 15 min |
| Semanal | Refinement con el Product Owner | 1 h |
| Cierre del sprint | Sprint Review (demo y aceptación) | 1 h |
| Cierre del sprint | Retrospectiva | 45 min |

## Reglas de convivencia en el código

- `libs/common/` lo tocan todos: **avisar en el Daily antes de modificarlo.**
- Cada quien trabaja en su carpeta; si necesita algo de otra, lo pide, no lo edita.
- Nada de credenciales en el repositorio. Todo por `.env`, que está en `.gitignore`.
- Los nombres de código en español, igual que el dominio del cliente. Es más fácil
  defender en la sustentación que el código y el tablero hablen el mismo idioma.
