import { ApiError } from './client'

const MESSAGES: Record<string, string> = {
  INVALID_CREDENTIALS: 'El correo o la contraseña no son correctos.',
  UNAUTHORIZED: 'Tu sesión terminó. Vuelve a iniciar sesión.',
  FORBIDDEN: 'No tienes permiso para realizar esta acción.',
  NOT_FOUND: 'No encontramos lo que buscas.',
  VALIDATION_ERROR: 'Revisa los datos ingresados.',
  CONFLICT: 'Esta acción ya se había realizado.',
  ML_SERVICE_UNAVAILABLE: 'El servicio de análisis no está disponible. Inténtalo en unos minutos.',
  EMAIL_NOT_SENT: 'El servidor de correo no respondió. Inténtalo de nuevo en unos minutos.',
  NO_FAMILY_CONTACT:
    'El estudiante no tiene un apoderado con correo registrado, así que no hay a quién enviarlo.',
  INVITATION_EXPIRED:
    'Este enlace ya no es válido: venció o ya se usó. Pide al colegio que te envíe uno nuevo.',
  INVITATION_NOT_FOUND:
    'Este enlace ya no es válido: venció o ya se usó. Pide al colegio que te envíe uno nuevo.',
  ALREADY_HAS_ACCESS: 'Este apoderado ya creó su contraseña; no necesita otra invitación.',
  FILE_TOO_LARGE: 'El archivo es demasiado grande. El límite es de 2 MB.',
  UNSUPPORTED_FILE_TYPE: 'Solo se aceptan archivos .csv o .xlsx.',
}

export function messageFor(error: unknown): string {
  if (error instanceof ApiError) return MESSAGES[error.code] ?? error.message
  return 'No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.'
}
