/**
 * Modal para registrar novo dispositivo.
 * 
 * Solicita:
 * - Chave de ativação
 * - Nome do dispositivo
 */

import { useState, FormEvent } from 'react'
import { X, Key, Smartphone, AlertCircle } from 'lucide-react'
import type { RegisterDeviceRequest } from '../types'

interface RegisterDeviceModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: RegisterDeviceRequest) => Promise<void>
  isLoading?: boolean
}

/**
 * RegisterDeviceModal Component
 * 
 * Modal para registrar um novo dispositivo com chave de ativação.
 */
export default function RegisterDeviceModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
}: RegisterDeviceModalProps) {
  const [activationKey, setActivationKey] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  if (!isOpen) return null

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')

    // Validação
    if (!activationKey || !name) {
      setError('Por favor, preencha todos os campos')
      return
    }

    try {
      await onSubmit({ activation_key: activationKey, name })
      // Limpa formulário após sucesso
      setActivationKey('')
      setName('')
      onClose()
    } catch (err: any) {
      setError(err.message || 'Erro ao registrar dispositivo')
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              Registrar Dispositivo
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
              disabled={isLoading}
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Mensagem de erro */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Formulário */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Chave de ativação */}
            <div>
              <label htmlFor="activation_key" className="label">
                Chave de Ativação
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Key className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="activation_key"
                  type="text"
                  value={activationKey}
                  onChange={(e) => setActivationKey(e.target.value.toUpperCase())}
                  className="input pl-10"
                  placeholder="XXXX-XXXX-XXXX-XXXX"
                  disabled={isLoading}
                  autoFocus
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Insira a chave de ativação fornecida pelo administrador
              </p>
            </div>

            {/* Nome do dispositivo */}
            <div>
              <label htmlFor="device_name" className="label">
                Nome do Dispositivo
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Smartphone className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="device_name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input pl-10"
                  placeholder="Ex: Sala de Estar"
                  disabled={isLoading}
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Escolha um nome descritivo para identificar o dispositivo
              </p>
            </div>

            {/* Botões */}
            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                disabled={isLoading}
                className="flex-1 btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Registrando...' : 'Registrar'}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={isLoading}
                className="flex-1 btn btn-secondary"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
