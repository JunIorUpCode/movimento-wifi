/**
 * Página de gerenciamento de licenças.
 * 
 * Funcionalidades:
 * - Listagem de licenças com filtros
 * - Formulário de geração de licença
 * - Exibir activation_key gerada (copiar para clipboard)
 * - Ações: revogar, estender licença
 */

export default function LicensesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Gerenciamento de Licenças</h1>
        <p className="text-gray-600 mt-1">
          Gere e gerencie licenças de ativação
        </p>
      </div>

      <div className="card">
        <p className="text-gray-500">
          Implementação completa será feita na subtarefa 12.5
        </p>
      </div>
    </div>
  )
}
