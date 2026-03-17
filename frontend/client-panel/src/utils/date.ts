/**
 * Utilitários para formatação de datas.
 */

/**
 * Formata uma data como "há X minutos/horas/dias"
 */
export function formatDistanceToNow(date: string | Date): string {
  const now = new Date()
  const past = new Date(date)
  const diffMs = now.getTime() - past.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSecs < 60) {
    return 'há poucos segundos'
  } else if (diffMins < 60) {
    return `há ${diffMins} ${diffMins === 1 ? 'minuto' : 'minutos'}`
  } else if (diffHours < 24) {
    return `há ${diffHours} ${diffHours === 1 ? 'hora' : 'horas'}`
  } else if (diffDays < 30) {
    return `há ${diffDays} ${diffDays === 1 ? 'dia' : 'dias'}`
  } else {
    return past.toLocaleDateString('pt-BR')
  }
}

/**
 * Formata uma data no formato brasileiro (DD/MM/YYYY HH:MM)
 */
export function formatDateTime(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Formata apenas a data no formato brasileiro (DD/MM/YYYY)
 */
export function formatDate(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/**
 * Formata apenas a hora (HH:MM)
 */
export function formatTime(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
