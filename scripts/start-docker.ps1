# Script para iniciar Docker Desktop automaticamente
# WiFiSense SaaS Multi-Tenant Platform

Write-Host "🐋 Iniciando Docker Desktop..." -ForegroundColor Cyan
Write-Host ""

# Verificar se Docker Desktop está instalado
$dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (-not (Test-Path $dockerPath)) {
    Write-Host "❌ Docker Desktop não encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor, instale o Docker Desktop:" -ForegroundColor Yellow
    Write-Host "https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Verificar se já está rodando
$dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
if ($dockerProcess) {
    Write-Host "✅ Docker Desktop já está rodando!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "🚀 Iniciando Docker Desktop..." -ForegroundColor Yellow
    Start-Process $dockerPath
    Write-Host "⏳ Aguardando Docker inicializar (60 segundos)..." -ForegroundColor Yellow
    
    # Aguardar 60 segundos
    for ($i = 60; $i -gt 0; $i--) {
        Write-Progress -Activity "Aguardando Docker" -Status "$i segundos restantes" -PercentComplete ((60-$i)/60*100)
        Start-Sleep -Seconds 1
    }
    Write-Progress -Activity "Aguardando Docker" -Completed
    Write-Host ""
}

# Verificar se Docker está respondendo
Write-Host "🔍 Verificando Docker..." -ForegroundColor Cyan
$maxAttempts = 10
$attempt = 0
$dockerReady = $false

while ($attempt -lt $maxAttempts -and -not $dockerReady) {
    $attempt++
    Write-Host "   Tentativa $attempt de $maxAttempts..." -ForegroundColor Gray
    
    try {
        $result = docker version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerReady = $true
            Write-Host "✅ Docker está pronto!" -ForegroundColor Green
            Write-Host ""
        } else {
            Start-Sleep -Seconds 3
        }
    } catch {
        Start-Sleep -Seconds 3
    }
}

if (-not $dockerReady) {
    Write-Host "❌ Docker não está respondendo após $maxAttempts tentativas" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possíveis soluções:" -ForegroundColor Yellow
    Write-Host "1. Aguarde mais alguns segundos e tente novamente" -ForegroundColor White
    Write-Host "2. Abra Docker Desktop manualmente" -ForegroundColor White
    Write-Host "3. Reinicie o computador" -ForegroundColor White
    Write-Host "4. Consulte: SOLUCAO_DOCKER_NAO_RODANDO.md" -ForegroundColor White
    Write-Host ""
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Mostrar informações do Docker
Write-Host "📊 Informações do Docker:" -ForegroundColor Cyan
docker version --format "   Docker Engine: {{.Server.Version}}"
Write-Host ""

# Testar com hello-world
Write-Host "🧪 Testando Docker com hello-world..." -ForegroundColor Cyan
docker run --rm hello-world 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Teste bem-sucedido!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Teste falhou, mas Docker está rodando" -ForegroundColor Yellow
}
Write-Host ""

# Perguntar se deseja iniciar infraestrutura
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
$response = Read-Host "Deseja iniciar a infraestrutura WiFiSense agora? (S/N)"

if ($response -eq "S" -or $response -eq "s") {
    Write-Host ""
    Write-Host "🚀 Iniciando infraestrutura..." -ForegroundColor Cyan
    Write-Host ""
    
    # Verificar se docker-compose.yml existe
    if (Test-Path "docker-compose.yml") {
        docker-compose up -d postgres redis rabbitmq
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Infraestrutura iniciada com sucesso!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Containers rodando:" -ForegroundColor Cyan
            docker-compose ps
            Write-Host ""
            Write-Host "Próximos passos:" -ForegroundColor Yellow
            Write-Host "1. Verificar health: make infra-health" -ForegroundColor White
            Write-Host "2. Verificar schemas: make db-check" -ForegroundColor White
            Write-Host "3. Testar auth-service: make test-auth" -ForegroundColor White
            Write-Host "4. Testar tenant-service: make test-tenant" -ForegroundColor White
            Write-Host "5. Teste completo: make test-integration" -ForegroundColor White
        } else {
            Write-Host ""
            Write-Host "❌ Erro ao iniciar infraestrutura" -ForegroundColor Red
            Write-Host "Verifique os logs: docker-compose logs" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Arquivo docker-compose.yml não encontrado!" -ForegroundColor Red
        Write-Host "Certifique-se de estar na pasta raiz do projeto" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "✅ Docker está pronto para uso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Para iniciar a infraestrutura manualmente:" -ForegroundColor Yellow
    Write-Host "   make infra-up" -ForegroundColor White
    Write-Host "   ou" -ForegroundColor Gray
    Write-Host "   docker-compose up -d postgres redis rabbitmq" -ForegroundColor White
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
