# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones según [SemVer](https://semver.org/lang/es/).

## [1.0.0] - 2026-11-04

Primera versión lista para entregarse a un colegio: cubre la operación diaria, el ciclo de vida del estudiante y del modelo, la privacidad legal y la calidad verificada.

### Para la dirección
- Resumen del colegio con semáforo de riesgo, aulas y factores más frecuentes; vista rápida y ficha completa de cada estudiante.
- Configuración del colegio: bimestres, cursos, personal (invitaciones por correo), aulas con tutor y asignación de cursos.
- Cierre de año con vista previa: promoción, repitentes y egresados.
- Retiros y traslados con motivo; aviso en la ficha y opción de revertir.
- Rendimiento del modelo frente a retiros reales y activación de versiones entrenadas por el área de análisis.
- Bandeja de solicitudes de datos (Ley N.° 29733) con plazo legal y expediente descargable.

### Para docentes y tutores
- Registro diario: asistencia por día, notas de sus cursos y conducta del aula.
- Alertas de riesgo, recomendaciones con revisión antes de enviarlas a la familia y actas de reuniones con la familia.
- Seguimiento semanal obligatorio con recordatorios y situaciones de contexto que adaptan los mensajes.

### Para el área de análisis
- Carga de datos en dos pasos (revisar y confirmar): estudiantes, notas, asistencia y apoderados.
- Evaluaciones de riesgo por bimestre y umbrales configurables.
- Dataset anonimizado y reentrenamiento del modelo con resultados reales del colegio.

### Para las familias
- Portal con el avance del bimestre (sin niveles de riesgo), sugerencias aprobadas, encuesta y seguimiento mensual.
- Aviso de privacidad, consentimiento y solicitudes de acceso, rectificación, cancelación u oposición.
- Correos automáticos de asistencia semanal, notas del bimestre y reconocimiento de asistencia perfecta.

### Cuentas y seguridad
- Invitaciones por correo, recuperación y cambio de contraseña; cada cambio cierra todas las sesiones.
- Límite de intentos fallidos, cabeceras de seguridad y configuración de producción validada al arrancar.
- Auditoría de dependencias en CI y Dependabot.

### Machine Learning
- Random Forest con VIF, SMOTE dentro de los folds y GridSearch; explicaciones locales por oclusión.
- Registro de versiones con modelo activo, comparación justa en casos reales reservados y vuelta atrás.

### Calidad
- 261 tests de API (cobertura 96 %), tests del servicio ML y 91 tests de componentes web.
- 13 pruebas E2E con Playwright y revisión de accesibilidad con axe-core.
- Todas las pantallas bajo 152 ms (p95) con 560 estudiantes; tests que impiden consultas N+1.

### Corregido
- La confirmación del primer seguimiento mensual de la familia desaparecía al guardarse.
- La imagen del servicio ML no instalaba las librerías de entrenamiento.
- Cerrar el año dos veces podía volver a promover a los mismos estudiantes.

## [0.4.0]
- Integración completa de API, servicio ML y frontend.

## [0.3.0]
- Servicio de Machine Learning con entrenamiento, predicción y explicaciones.

## [0.2.0]
- API base: autenticación, datos académicos, asistencia, encuestas y actas.

## [0.1.0]
- Arquitectura, ADRs iniciales y entorno local con Docker Compose.

[1.0.0]: https://github.com/edutrackIA/edutrack/compare/v0.4.0...v1.0.0
