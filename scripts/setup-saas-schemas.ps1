# Script para criar schemas SaaS no banco wifi_movimento existente
# WiFiSense SaaS Multi-Tenant Platform

Write-Host "🔧 Criando schemas SaaS no banco wifi_movimento..." -ForegroundColor Cyan
Write-Host ""

# Configurações do banco (do backend/.env)
$DB_HOST = "localhost"
$DB_PORT = "5432"
$DB_NAME = "wifi_movimento"
$DB_USER = "postgres"
$DB_PASSWORD = "NovaSenhaForte123!"

# Definir variável de ambiente para senha
$env:PGPASSWORD = $DB_PASSWORD

Write-Host "📊 Conectando ao banco de dados..." -ForegroundColor Yellow
Write-Host "   Host: $DB_HOST" -ForegroundColor Gray
Write-Host "   Porta: $DB_PORT" -ForegroundColor Gray
Write-Host "   Banco: $DB_NAME" -ForegroundColor Gray
Write-Host "   Usuário: $DB_USER" -ForegroundColor Gray
Write-Host ""

# Verificar se psql está disponível
$psqlPath = Get-Command psql -ErrorAction SilentlyContinue
if (-not $psqlPath) {
    Write-Host "❌ psql não encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Opções:" -ForegroundColor Yellow
    Write-Host "1. Instalar PostgreSQL client tools" -ForegroundColor White
    Write-Host "2. Ou executar manualmente:" -ForegroundColor White
    Write-Host "   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f scripts/create-saas-schemas.sql" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

# Executar script SQL
Write-Host "🚀 Executando script de criação de schemas..." -ForegroundColor Cyan
try {
    $result = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f scripts/create-saas-schemas.sql 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Schemas criados com sucesso!" -ForegroundColor Green
        Write-Host ""
        
        # Listar schemas criados
        Write-Host "📋 Schemas SaaS criados:" -ForegroundColor Cyan
        $schemas = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE '%_schema' ORDER BY schema_name;"
        
        foreach ($schema in $schemas) {
            $schema = $schema.Trim()
            if ($schema) {
                Write-Host "   ✅ $schema" -ForegroundColor Green
            }
        }
        
        Write-Host ""
        Write-Host "🎉 Setup concluído!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Próximos passos:" -ForegroundColor Yellow
        Write-Host "1. Atualizar .env na raiz do projeto" -ForegroundColor White
        Write-Host "2. Executar testes: python scripts/test-integration-simple.py" -ForegroundColor White
        Write-Host ""
        
    } else {
        Write-Host ""
        Write-Host "❌ Erro ao criar schemas!" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
        Write-Host ""
        exit 1
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Erro: $_" -ForegroundColor Red
    Write-Host ""
    exit 1
} finally {
    # Limpar variável de senha
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}
