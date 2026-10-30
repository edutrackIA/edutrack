# Seguridad en EduTrack

EduTrack maneja datos de menores de edad, así que la seguridad y la privacidad son requisitos, no extras. Este documento resume las medidas y dónde están implementadas.

## Medidas por riesgo (OWASP Top 10, 2021)

| Riesgo | Medida |
|---|---|
| **A01 Control de acceso** | RBAC más pertenencia: cada endpoint verifica el rol y que el recurso sea de la institución, del aula tutorada o del hijo del apoderado (`access_policy.py`, ADR-0004). Las familias nunca ven niveles de riesgo ni probabilidades. |
| **A02 Fallas criptográficas** | Contraseñas con bcrypt. Los tokens de invitación y de refresco se guardan solo como hash SHA-256. En producción se exige HTTPS (HSTS) y un secreto JWT aleatorio. |
| **A03 Inyección** | SQLAlchemy con consultas parametrizadas; validación de entrada con Pydantic; los archivos importados se leen como datos, nunca se ejecutan. |
| **A04 Diseño inseguro** | Situaciones sensibles con lista cerrada y sin texto clínico (ADR-0009); los mensajes a familias pasan por revisión del tutor. |
| **A05 Configuración** | La API no arranca en producción con valores de desarrollo; la documentación interactiva se desactiva en producción; CORS limitado a métodos y cabeceras necesarios; cabeceras de seguridad en cada respuesta. |
| **A06 Componentes vulnerables** | `pip-audit` y `npm audit` en cada PR; Dependabot semanal. |
| **A07 Autenticación** | Tokens de acceso de 15 minutos con refresco rotativo y detección de reuso (ADR-0008); límite de intentos fallidos (ADR-0012); el login no revela qué cuentas existen. |
| **A08 Integridad** | Migraciones versionadas con Alembic; CI obligatorio antes de mergear. |
| **A09 Registro** | Auditoría de cambios en situaciones de contexto; registro de avisos enviados al personal. |
| **A10 SSRF** | La API solo llama al servicio ML interno, con URL fija por configuración. |

## Datos personales (Ley N.° 29733)

- Dataset de entrenamiento sintético (ADR-0005).
- Encuesta sociofamiliar visible solo para dirección y análisis.
- Informes psicológicos fuera del sistema; solo se registra "en seguimiento".

## Reportar una vulnerabilidad

Si encuentras un problema de seguridad, no abras un issue público. Escribe al responsable del repositorio con los detalles y los pasos para reproducirlo.
