# ADR-0012: Límite de intentos fallidos en memoria

- **Estado:** Aceptado
- **Fecha:** 2026-10-30

## Contexto
El login y los enlaces de invitación son públicos. Sin límite, alguien podría probar contraseñas de un apoderado o docente sin restricción.

## Decisión
- Ventana deslizante de 15 minutos sobre **intentos fallidos**:
  - 5 por cuenta y dirección IP (adivinar la contraseña de una persona).
  - 30 por dirección IP (probar muchas cuentas desde el mismo lugar).
  - 20 enlaces de invitación inválidos por dirección IP.
- Al superar el límite se responde `429 TOO_MANY_ATTEMPTS` con `Retry-After`. Un login correcto reinicia el contador de esa cuenta.
- Los contadores viven en la memoria del proceso de la API.

## Consecuencias
- Suficiente para una sola instancia de la API, que es el despliegue previsto (EC2).
- Con varias instancias detrás de un balanceador, los contadores deben pasar a Redis, y el proxy debe reenviar la IP real del cliente.
- Bloquear por cuenta y por IP, y no solo por cuenta, evita que un atacante bloquee a voluntad la cuenta de otra persona desde cualquier lugar.
