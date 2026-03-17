/**
 * Componente de card de status de dispositivo.
 * 
 * Exibe:
 * - Nome do dispositivo
 * - Status (online/offline)
 * - Last seen
 * - Tipo de hardware
 * - Métricas de saúde (CPU, memória, disco)
 */

import { Smartphone, Wifi, WifiOff, Clock, Cpu, HardDrive, MemoryStick } from 'lucide-react'
import type { Device } from '../types'
import { formatDistanceToNow } from '../utils/date'

interface DeviceStatusCardProps {
  device: Device
}

/**
 * DeviceStatusCard Component
 * 
 * Card visual para exibir status e informações de um dispositivo.
 */
export default function DeviceStatusCard({ device }: DeviceStatusCardProps) {
  const isOnline = device.status === 'online'
  const isError = device.status === 'error'

  return (
    <div className="card hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center">
          <div className={`p-2 rounded-lg ${
            isOnline ? 'bg-green-100' : isError ? 'bg-red-100' : 'bg-gray-100'
          }`}>
            <Smartphone className={`w-5 h-5 ${
              isOnline ? 'text-green-600' : isError ? 'text-red-600' : 'text-gray-600'
            }`} />
          </div>
          <div className="ml-3">
            <h3 className="text-lg font-semibold text-gray-900">{device.name}</h3>
            <p className="text-sm text-gray-500 capitalize">{device.hardware_type.replace('_', ' ')}</p>
          </div>
        </div>

        {/* Status badge */}
        <span className={`badge ${
          isOnline ? 'badge-success' : isError ? 'badge-danger' : 'badge-warning'
        }`}>
          {isOnline ? (
            <>
              <Wifi className="w-3 h-3 mr-1" />
              Online
            </>
          ) : (
            <>
              <WifiOff className="w-3 h-3 mr-1" />
              {isError ? 'Erro' : 'Offline'}
            </>
          )}
        </span>
      </div>

      {/* Last seen */}
      <div className="flex items-center text-sm text-gray-600 mb-4">
        <Clock className="w-4 h-4 mr-2" />
        <span>
          Visto {formatDistanceToNow(device.last_seen)}
        </span>
      </div>

      {/* Hardware info */}
      {device.hardware_info && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs font-medium text-gray-700 mb-2">Hardware</p>
          <div className="space-y-1">
            <p className="text-xs text-gray-600">
              <span className="font-medium">OS:</span> {device.hardware_info.os}
            </p>
            <p className="text-xs text-gray-600">
              <span className="font-medium">Adaptador:</span> {device.hardware_info.wifi_adapter}
            </p>
            <p className="text-xs text-gray-600">
              <span className="font-medium">CSI:</span>{' '}
              {device.hardware_info.csi_capable ? (
                <span className="text-green-600">Suportado</span>
              ) : (
                <span className="text-gray-500">Não suportado</span>
              )}
            </p>
          </div>
        </div>
      )}

      {/* Health metrics */}
      {device.health && (
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-blue-50 rounded">
            <Cpu className="w-4 h-4 mx-auto mb-1 text-blue-600" />
            <p className="text-xs font-medium text-blue-900">{device.health.cpu_percent.toFixed(0)}%</p>
            <p className="text-xs text-blue-600">CPU</p>
          </div>
          <div className="text-center p-2 bg-purple-50 rounded">
            <MemoryStick className="w-4 h-4 mx-auto mb-1 text-purple-600" />
            <p className="text-xs font-medium text-purple-900">{device.health.memory_mb.toFixed(0)} MB</p>
            <p className="text-xs text-purple-600">RAM</p>
          </div>
          <div className="text-center p-2 bg-orange-50 rounded">
            <HardDrive className="w-4 h-4 mx-auto mb-1 text-orange-600" />
            <p className="text-xs font-medium text-orange-900">{device.health.disk_percent.toFixed(0)}%</p>
            <p className="text-xs text-orange-600">Disco</p>
          </div>
        </div>
      )}
    </div>
  )
}
