# ADR-0004: Autenticación JWT y control de acceso por roles

- **Estado:** Aceptado
- **Fecha:** 2026-10-24

## Contexto
El sistema maneja datos académicos y sociofamiliares de menores de edad (Ley N.° 29733). Cada rol solo debe ver la información que le corresponde.

## Decisión
- Se usa un access token JWT de vida corta (15 min) y un refresh token rotativo (7 días) almacenado como hash.
- Los roles son `DIRECTOR`, `TEACHER`, `PARENT` y `ANALYST`. El tutor es un `TEACHER` asignado como tutor de un aula.
- La autorización se aplica en dos niveles:
  1. **Por rol**, para decidir qué endpoints puede usar cada usuario.
  2. **Por pertenencia**: un docente solo accede a sus aulas, un padre solo a sus hijos, y todos solo a su institución.
- Las contraseñas se guardan con hash bcrypt.

## Consecuencias
- Cada endpoint de lectura de estudiantes debe validar la pertenencia, no solo el rol. Esto se cubre con tests específicos.
