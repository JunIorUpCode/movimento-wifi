# 🚀 Início Rápido - WiFiSense SaaS

## Problema Atual

```
❌ Docker não está rodando
failed to connect to the docker API at npipe:////./pipe/docker_engine
```

## ✅ Solução em 3 Passos

### Passo 1: Abrir Docker Desktop

**Opção A: Menu Iniciar**
1. Pressione `Win + S`
2. Digite "Docker Desktop"
3. Clique para abrir
4. Aguarde o ícone da baleia 🐋 aparecer na bandeja (canto inferior direito)

**Opção B: Script Automático**
```powershell
# Executar no PowerShell
.\scripts\start-docker.ps1
```

### Passo 2: Aguardar Inicialização

- Observe o ícone da baleia na bandeja do sistema
- Quando parar de piscar = Docker está pronto
- Tempo estimado: 30-60 segundos

### Passo 3: Testar Docker

```powershell
# Testar
docker run hello-world
```

**Resultado esperado:**
```
Hello from Docker!
✅ Funcionou!
```

## 🎯 Após Docker Iniciar

### Opção 1: Automático (Recomendado)

```powershell
# Executar script
.\scripts\start-docker.ps1

# Quando perguntar "Deseja iniciar infraestrutura?", digite: S
```

### Opção 2: Manual

```bash
# 1. Iniciar infraestrutura
make infra-up

# 2. Verificar status
make infra-health

# 3. Testar auth-service
make test-auth

# 4. Testar tenant-service
make test-tenant

# 5. Teste completo
make test-integration
```

## 📋 Checklist Rápido

- [ ] Docker Desktop aberto
- [ ] Ícone da baleia visível (não piscando)
- [ ] `docker run hello-world` funciona
- [ ] Infraestrutura iniciada (postgres, redis, rabbitmq)
- [ ] Testes passando

## ❓ Problemas?

### Docker não abre
```powershell
# Iniciar manualmente
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### Docker não encontrado
- Instalar: https://www.docker.com/products/docker-desktop/
- Reiniciar computador após instalação

### Erro de WSL 2
```powershell
# PowerShell como Administrador
wsl --install
wsl --update
Restart-Computer
```

## 📚 Documentação Completa

- **Instalação Docker:** `GUIA_INSTALACAO_DOCKER.md`
- **Solução de problemas:** `SOLUCAO_DOCKER_NAO_RODANDO.md`
- **Testes:** `GUIA_TESTE_RAPIDO.md`
- **Checkpoint:** `TASK_4_CHECKPOINT_COMPLETO.md`

## 🆘 Ajuda Rápida

```powershell
# Ver comandos disponíveis
make help

# Status dos containers
docker ps

# Logs
docker-compose logs -f

# Parar tudo
docker-compose down
```

---

**Próximo passo:** Após Docker funcionar, execute `make test-integration` para validar tudo! 🎉
