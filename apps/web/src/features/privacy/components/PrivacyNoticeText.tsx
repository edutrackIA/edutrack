/**
 * Privacy notice (Ley N.° 29733). TEMPLATE: before a real deployment the school must
 * fill in its legal data and have the text reviewed by a lawyer. Changing the content
 * requires raising PRIVACY_NOTICE_VERSION in the API so guardians accept it again.
 */
export function PrivacyNoticeText() {
  const sections: [string, string[]][] = [
    [
      'Quién trata los datos',
      [
        'El colegio es el titular del banco de datos de sus estudiantes y familias. EduTrack es la herramienta que el colegio usa para ese tratamiento.',
      ],
    ],
    [
      'Qué datos se tratan',
      [
        'Datos del estudiante: nombre, código, fecha de nacimiento, aula, notas, asistencia, conducta y estado de matrícula.',
        'Datos que comparte la familia: encuesta familiar del bimestre (horas de estudio, acceso a internet y dispositivo, comunicación familiar, trabajo del estudiante, tamaño del hogar) y el seguimiento mensual.',
        'Datos de los apoderados: nombre y correo.',
      ],
    ],
    [
      'Para qué se usan',
      [
        'Acompañar el aprendizaje y detectar a tiempo a estudiantes que podrían dejar de estudiar.',
        'Un modelo de Machine Learning estima el riesgo de cada estudiante. Sus resultados son orientativos: ninguna decisión se toma de forma automática y las recomendaciones a las familias siempre las revisa el tutor.',
        'Enviar a la familia información sobre asistencia, notas y sugerencias de acompañamiento.',
      ],
    ],
    [
      'Quién puede verlos',
      [
        'Solo el personal autorizado del colegio, según su función. La familia nunca ve niveles de riesgo ni probabilidades.',
        'Los datos no se venden ni se comparten con terceros para otros fines. Para mejorar el modelo solo se usan datos anonimizados, sin nombres ni códigos.',
      ],
    ],
    [
      'Cuánto tiempo se conservan',
      [
        'Mientras el estudiante esté matriculado y luego el tiempo que exijan las normas educativas para los registros académicos.',
      ],
    ],
    [
      'Sus derechos',
      [
        'Puede pedir acceso, rectificación, cancelación u oposición desde "Mi cuenta". El colegio responde dentro de los plazos de la Ley N.° 29733 y su reglamento.',
        'Si considera que no se atendió su solicitud, puede acudir a la Autoridad Nacional de Protección de Datos Personales.',
      ],
    ],
  ]

  return (
    <div className="flex flex-col gap-6">
      {sections.map(([title, paragraphs]) => (
        <section key={title}>
          <h2 className="font-figure text-xl font-semibold text-ink">{title}</h2>
          {paragraphs.map((paragraph) => (
            <p key={paragraph} className="mt-2 text-ink">
              {paragraph}
            </p>
          ))}
        </section>
      ))}
    </div>
  )
}
