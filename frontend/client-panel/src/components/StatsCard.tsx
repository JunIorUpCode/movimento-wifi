/**
 * Componente de card de estatísticas.
 * 
 * Exibe uma métrica com ícone, valor e label.
 */

import { LucideIcon } from 'lucide-react'

interface StatsCardProps {
  icon: LucideIcon
  label: string
  value: string | number
  color?: 'blue' | 'green' | 'orange' | 'red' | 'purple'
  isLoading?: boolean
}

/**
 * StatsCard Component
 * 
 * Card visual para exibir uma estatística com ícone.
 */
export default function StatsCard({
  icon: Icon,
  label,
  value,
  color = 'blue',
  isLoading,
}: StatsCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    orange: 'bg-orange-100 text-orange-600',
    red: 'bg-red-100 text-red-600',
    purple: 'bg-purple-100 text-purple-600',
  }

  if (isLoading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="w-12 h-12 bg-gray-200 rounded-lg mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className={`inline-flex p-3 rounded-lg ${colorClasses[color]} mb-4`}>
        <Icon className="w-6 h-6" />
      </div>
      <p className="text-3xl font-bold text-gray-900 mb-1">{value}</p>
      <p className="text-sm text-gray-600">{label}</p>
    </div>
  )
}
