# Guía de contribución

## Ramas

| Rama | Propósito |
|---|---|
| `main` | Código estable y versionado (tags SemVer) |
| `develop` | Integración de funcionalidades terminadas |
| `feature/<nombre>` | Nueva funcionalidad, creada desde `develop` |
| `fix/<nombre>` | Corrección de errores, creada desde `develop` |
| `release/<versión>` | Preparación de una versión, de `develop` a `main` |
| `hotfix/<nombre>` | Corrección urgente, creada desde `main` |

Usa nombres de rama en minúsculas y con guiones, por ejemplo `feature/auth-jwt-rbac`.

## Flujo

1. `git checkout develop && git pull`
2. `git checkout -b feature/<nombre>`
3. Haz commits pequeños y atómicos.
4. `git push -u origin feature/<nombre>`
5. Abre un Pull Request hacia `develop`. El CI debe estar en verde antes del merge.
6. Elimina la rama después del merge.

## Commits

Se sigue [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

**Tipos:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Scopes:** `web`, `api`, `ml`, `auth`, `db`, `infra`, `docs`, `deps`

Reglas:
- La descripción va en inglés, en imperativo, en minúsculas y sin punto final.
- Máximo 72 caracteres en la primera línea.
- Un cambio incompatible se indica con `!` o con `BREAKING CHANGE:` en el pie.

Ejemplos:
```
feat(auth): add jwt access and refresh tokens
fix(web): correct risk badge color on dashboard
test(ml): cover smote resampling on training split
```

## Hooks locales

```bash
pip install pre-commit
pre-commit install --hook-type pre-commit --hook-type commit-msg
```
