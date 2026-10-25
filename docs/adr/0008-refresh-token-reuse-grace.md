# ADR-0008: Margen de gracia en la rotación de refresh tokens

- **Estado:** Aceptado
- **Fecha:** 2026-10-26

## Contexto
Cada uso de un refresh token lo invalida y emite uno nuevo. Si se reutiliza un token invalidado, se asume que fue robado y se cierran todas las sesiones del usuario (ADR-0004). Al recargar la página varias veces seguidas, el navegador puede enviar un token que el servidor ya rotó pero cuya respuesta nunca llegó, y el usuario pierde la sesión sin motivo.

## Decisión
- Los tokens invalidados por rotación quedan marcados como `rotated`.
- Si un token rotado se reutiliza dentro de 30 segundos (`API_REFRESH_REUSE_GRACE_SECONDS`), se emite un par nuevo sin cerrar las demás sesiones.
- Fuera de ese margen, o si el token fue invalidado por un cierre de sesión, se mantiene la detección de robo.
- El frontend guarda el access token en `sessionStorage` para no rotar en cada recarga.

## Consecuencias
- Un token robado podría usarse durante los 30 segundos posteriores a su rotación. Es el mismo compromiso que aplican proveedores de identidad con "reuse interval".
- Las recargas rápidas ya no cierran la sesión.
