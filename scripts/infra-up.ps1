# Script para iniciar infraestrutura WiFiSense
# Equivalente a: make infra-up

Write-Host "🚀 Iniciando infraestrutura WiFiSense..." -ForegroundColor Cyan
Write-Host ""

# Verificar se Docker está rodando
try {
    docker version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker não está respondendo"
    }
} catch {
    Write-Host "❌ Docker não está rodando!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Execute primeiro:" -ForegroundColor Yellow
    Write-Host "   .\scripts\start-docker.ps1" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Verificar se docker-compose.yml existe
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ Arquivo docker-compose.yml não encontrado!" -ForegroundColor Red
    Write-Host "Certifique-se de estar na pasta raiz do projeto" -ForegroundColor Yellow
    exit 1
}

# Iniciar infraestrutura
Write-Host "📦 Iniciando PostgreSQL, Redis e RabbitMQ..." -ForegroundColor Yellow
docker-compose up -d postgres redis rabbitmq

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Infraestrutura iniciada!" -ForegroundColor Green
    Write-Host ""
    Write-Host "⏳ Aguardando serviços ficarem prontos (10 segundos)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    Write-Host ""
    
    # Verificar status
    Write-Host "📊 Status dos containers:" -ForegroundColor Cyan
    docker-compose ps postgres redis rabbitmq
    Write-Host ""
    
    Write-Host "✅ Pronto!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos passos:" -ForegroundColor Yellow
    Write-Host "   .\scripts\infra-health.ps1    # Verificar health" -ForegroundColor White
    Write-Host "   .\scripts\db-check.ps1        # Verificar schemas" -ForegroundColor White
    Write-Host "   .\scripts\test-auth.ps1       # Testar auth-service" -ForegroundColor White
    Write-Host "   .\scripts\test-tenant.ps1     # Testar tenant-service" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Erro ao iniciar infraestrutura" -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifique os logs:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs postgres" -ForegroundColor White
    Write-Host "   docker-compose logs redis" -ForegroundColor White
    Write-Host "   docker-compose logs rabbitmq" -ForegroundColor White
    Write-Host ""
    exit 1
}
