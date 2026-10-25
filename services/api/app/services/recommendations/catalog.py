"""Recommendation catalog: which action to suggest for each risk factor.

Family messages never mention risk levels or probabilities: they describe concrete,
positive actions. Teacher actions are operational and only visible to staff.
"""

ML_DISCLAIMER = (
    "Estas recomendaciones fueron generadas automáticamente por EduTrack mediante un "
    "modelo de Machine Learning que analiza notas, asistencia, conducta y la encuesta "
    "familiar, y fueron revisadas por el tutor. Son orientativas y no reemplazan su "
    "evaluación. Si tiene dudas, puede coordinar una reunión con el tutor desde el portal."
)

PARENT_ACTIONS = {
    "attendance_rate": (
        "Asistencia: {name} ha faltado a varias clases este bimestre. Le sugerimos conversar "
        "sobre los motivos de las faltas y asegurar su asistencia diaria."
    ),
    "late_count": (
        "Puntualidad: {name} registró varias tardanzas. Establecer una rutina fija por las "
        "mañanas puede ayudarle a llegar a tiempo."
    ),
    "failed_subjects": (
        "Cursos a reforzar: {subjects}. Acordar un horario fijo de estudio en casa, de al "
        "menos una hora diaria, puede ayudarle mucho."
    ),
    "avg_score": (
        "Rendimiento: revisar juntos cada semana los cuadernos y tareas de {name} le ayudará "
        "a mantenerse al día en sus cursos."
    ),
    "score_trend": (
        "Cambio reciente: las notas de {name} bajaron respecto al bimestre anterior. Conversar "
        "sobre qué cambió puede ayudar a identificar dificultades a tiempo."
    ),
    "behavior_rating": (
        "Convivencia: conversar en casa sobre el respeto y la participación en clase será de "
        "gran apoyo para {name}."
    ),
    "study_hours_week": (
        "Hábitos de estudio: dedicar más tiempo al estudio en casa, en un espacio tranquilo y "
        "sin distracciones, puede marcar la diferencia."
    ),
    "family_communication": (
        "Comunicación: dedicar unos minutos al día a conversar con {name} sobre cómo le va en "
        "el colegio fortalece su motivación."
    ),
    "student_works": (
        "Equilibrio: si {name} realiza actividades laborales, le recomendamos coordinar con el "
        "tutor para equilibrarlas con sus estudios."
    ),
    "home_internet": (
        "Recursos: si no cuentan con internet en casa, el tutor puede orientarles sobre "
        "espacios con acceso para realizar las tareas."
    ),
    "has_study_device": (
        "Recursos: si {name} no cuenta con un dispositivo para estudiar, puede consultar con "
        "el tutor sobre las alternativas del colegio."
    ),
}

TEACHER_ACTIONS = {
    "attendance_rate": "Contactar a la familia y registrar el motivo de las inasistencias.",
    "late_count": "Conversar con el estudiante sobre la puntualidad e informar a la familia.",
    "failed_subjects": "Derivar a reforzamiento en: {subjects}.",
    "avg_score": "Revisar con el estudiante la organización de sus tareas y cuadernos.",
    "score_trend": "Realizar una entrevista individual para identificar qué cambió.",
    "behavior_rating": "Registrar las incidencias y coordinar con convivencia escolar.",
    "study_hours_week": "Asignar tareas cortas con seguimiento semanal.",
    "family_communication": "Programar una reunión con la familia.",
    "student_works": "Coordinar con bienestar estudiantil o psicología.",
    "home_internet": "Verificar el acceso a recursos y orientar sobre alternativas del colegio.",
    "has_study_device": "Verificar el acceso a recursos y orientar sobre alternativas del colegio.",
}

PARENT_POSITIVE = [
    "Buen desempeño: {name} mantiene un buen rendimiento este bimestre. ¡Sigan acompañándole "
    "con la misma dedicación!",
    "Próximas metas: conversar sobre sus objetivos para el siguiente bimestre le ayudará a "
    "seguir creciendo.",
]
PARENT_FOLLOW_UP = (
    "Seguimiento: su tutor, {tutor}, estará atento al avance de {name}. Puede coordinar una "
    "reunión desde el portal."
)
TEACHER_ROUTINE = "Mantener el seguimiento regular."

MAX_PARENT_ACTIONS = 3
