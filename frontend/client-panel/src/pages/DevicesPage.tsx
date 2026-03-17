/**
 * Página de gerenciamento de dispositivos.
 * 
 * Exibe:
 * - Listagem de dispositivos do tenant
 * - Formulário de registro (solicitar activation_key)
 * - Ações: renomear, configurar, remover dispositivo
 * - Visualização de hardware_info e métricas de saúde
 */

import { useState } from 'react'
import { Plus, Smartphone, Edit2, Trash2, Settings } from 'lucide-react'
import { useDevices, useRegisterDevice, useUpdateDevice, useDeleteDevice } from '../hooks/useDevices'
import DeviceStatusCard from '../components/DeviceStatusCard'
import RegisterDeviceModal from '../components/RegisterDeviceModal'

export default function DevicesPage() {
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false)
  const [editingDevice, setEditingDevice] = useState<string | null>(null)
  const [newName, setNewName] = useState('')

  // Hooks
  const { data: devices, isLoading } = useDevices()
  const registerDevice = useRegisterDevice()
  const updateDevice = useUpdateDevice()
  const deleteDevice = useDeleteDevice()

  // Handler para registrar dispositivo
  const handleRegister = async (data: { activation_key: string; name: string }) => {
    await registerDevice.mutateAsync(data)
  }

  // Handler para renomear dispositivo
  const handleRename = async (deviceId: string) => {
    if (!newName.trim()) return

    try {
      await updateDevice.mutateAsync({
        id: deviceId,
        data: { name: newName },
      })
      setEditingDevice(null)
      setNewName('')
    } catch (error) {
      console.error('Erro ao renomear dispositivo:', error)
    }
  }

  // Handler para deletar dispositivo
  const handleDelete = async (deviceId: string, deviceName: string) => {
    if (!confirm(`Tem certeza que deseja remover o dispositivo "${deviceName}"?`)) {
      return
    }

    try {
      await deleteDevice.mutateAsync(deviceId)
    } catch (error) {
      console.error('Erro ao deletar dispositivo:', error)
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dispositivos</h1>
          <p className="text-gray-600 mt-1">
            Gerencie seus dispositivos de monitoramento
          </p>
        </div>
        <button
          onClick={() => setIsRegisterModalOpen(true)}
          className="btn btn-primary flex items-center"
        >
          <Plus className="w-5 h-5 mr-2" />
          Registrar Dispositivo
        </button>
      </div>

      {/* Lista de dispositivos */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-48 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : !devices || devices.length === 0 ? (
        <div className="card text-center py-12">
          <Smartphone className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhum dispositivo registrado
          </h3>
          <p className="text-gray-600 mb-6">
            Registre seu primeiro dispositivo para começar a monitorar
          </p>
          <button
            onClick={() => setIsRegisterModalOpen(true)}
            className="btn btn-primary inline-flex items-center"
          >
            <Plus className="w-5 h-5 mr-2" />
            Registrar Dispositivo
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {devices.map((device) => (
            <div key={device.id} className="relative">
              <DeviceStatusCard device={device} />

              {/* Ações */}
              <div className="absolute top-4 right-4 flex gap-2">
                {/* Botão de editar */}
                <button
                  onClick={() => {
                    setEditingDevice(device.id)
                    setNewName(device.name)
                  }}
                  className="p-2 bg-white rounded-lg shadow hover:bg-gray-50 transition-colors"
                  title="Renomear"
                >
                  <Edit2 className="w-4 h-4 text-gray-600" />
                </button>

                {/* Botão de deletar */}
                <button
                  onClick={() => handleDelete(device.id, device.name)}
                  className="p-2 bg-white rounded-lg shadow hover:bg-red-50 transition-colors"
                  title="Remover"
                >
                  <Trash2 className="w-4 h-4 text-red-600" />
                </button>
              </div>

              {/* Modal inline de edição */}
              {editingDevice === device.id && (
                <div className="absolute inset-0 bg-white rounded-lg shadow-lg p-4 z-10">
                  <h4 className="text-sm font-semibold text-gray-900 mb-3">
                    Renomear Dispositivo
                  </h4>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="input mb-3"
                    placeholder="Novo nome"
                    autoFocus
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRename(device.id)}
                      disabled={updateDevice.isPending}
                      className="flex-1 btn btn-primary text-sm"
                    >
                      {updateDevice.isPending ? 'Salvando...' : 'Salvar'}
                    </button>
                    <button
                      onClick={() => {
                        setEditingDevice(null)
                        setNewName('')
                      }}
                      disabled={updateDevice.isPending}
                      className="flex-1 btn btn-secondary text-sm"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Modal de registro */}
      <RegisterDeviceModal
        isOpen={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
        onSubmit={handleRegister}
        isLoading={registerDevice.isPending}
      />

      {/* Informações adicionais */}
      {devices && devices.length > 0 && (
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start">
            <Settings className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="ml-3">
              <p className="text-sm text-blue-800">
                <span className="font-medium">Dica:</span> Você pode renomear ou remover dispositivos
                usando os botões no canto superior direito de cada card.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
