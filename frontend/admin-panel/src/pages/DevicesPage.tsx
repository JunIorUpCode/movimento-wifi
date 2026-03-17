/**
 * Página de monitoramento de dispositivos.
 * 
 * Funcionalidades:
 * - Listagem de todos os dispositivos com status (online/offline)
 * - Filtros por tenant, status, plano
 * - Visualização de métricas de saúde (CPU, memória, disco)
 * - Indicador visual de last_seen
 */

export default function DevicesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Monitoramento de Dispositivos</h1>
        <p className="text-gray-600 mt-1">
          Visualize status e saúde de todos os dispositivos
        </p>
      </div>

      <div className="card">
        <p className="text-gray-500">
          Implementação completa será feita na subtarefa 12.6
        </p>
      </div>
    </div>
  )
}
