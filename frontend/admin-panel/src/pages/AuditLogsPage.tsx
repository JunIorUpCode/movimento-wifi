/**
 * Página de audit logs.
 * 
 * Funcionalidades:
 * - Listagem de logs com filtros (ação, recurso, data)
 * - Exibir: timestamp, admin, ação, recurso, before/after state
 * - Paginação e busca
 */

export default function AuditLogsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
        <p className="text-gray-600 mt-1">
          Histórico de ações administrativas
        </p>
      </div>

      <div className="card">
        <p className="text-gray-500">
          Implementação completa será feita na subtarefa 12.7
        </p>
      </div>
    </div>
  )
}
