import { ApiError } from './client'

const MESSAGES: Record<string, string> = {
  INVALID_CREDENTIALS: 'El correo o la contraseña no son correctos.',
  UNAUTHORIZED: 'Tu sesión terminó. Vuelve a iniciar sesión.',
  FORBIDDEN: 'No tienes permiso para realizar esta acción.',
  NOT_FOUND: 'No encontramos lo que buscas.',
  VALIDATION_ERROR: 'Revisa los datos ingresados.',
  CONFLICT: 'Esta acción ya se había realizado.',
  ML_SERVICE_UNAVAILABLE: 'El servicio de análisis no está disponible. Inténtalo en unos minutos.',
  EMAIL_NOT_SENT: 'No se pudo enviar el correo. Inténtalo de nuevo.',
  FILE_TOO_LARGE: 'El archivo es demasiado grande. El límite es de 2 MB.',
  UNSUPPORTED_FILE_TYPE: 'Solo se aceptan archivos .csv o .xlsx.',
}

export function messageFor(error: unknown): string {
  if (error instanceof ApiError) return MESSAGES[error.code] ?? error.message
  return 'No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.'
}
