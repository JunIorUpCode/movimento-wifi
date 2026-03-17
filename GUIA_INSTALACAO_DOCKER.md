# 🐳 Guia de Instalação do Docker no Windows

## Passo 1: Baixar Docker Desktop

1. Acesse: https://www.docker.com/products/docker-desktop/
2. Clique em "Download for Windows"
3. Execute o instalador `Docker Desktop Installer.exe`

## Passo 2: Requisitos do Sistema

### Windows 10/11 Pro, Enterprise ou Education
- WSL 2 (Windows Subsystem for Linux 2)
- Virtualização habilitada na BIOS

### Windows 10/11 Home
- WSL 2 instalado
- Atualização do Windows 10 versão 2004 ou superior

## Passo 3: Instalar WSL 2

Abra PowerShell como Administrador e execute:

```powershell
# Habilitar WSL
wsl --install

# Reiniciar o computador
Restart-Computer
```

Após reiniciar:

```powershell
# Verificar versão do WSL
wsl --list --verbose

# Definir WSL 2 como padrão
wsl --set-default-version 2
```

## Passo 4: Instalar Docker Desktop

1. Execute o instalador baixado
2. Marque a opção "Use WSL 2 instead of Hyper-V"
3. Clique em "Ok" e aguarde a instalação
4. Reinicie o computador quando solicitado

## Passo 5: Verificar Instalação

Abra PowerShell ou CMD e execute:

```bash
# Verificar versão do Docker
docker --version

# Verificar Docker Compose
docker-compose --version

# Testar Docker
docker run hello-world
```

Se aparecer "Hello from Docker!", a instalação foi bem-sucedida!

## Passo 6: Configurar Docker Desktop

1. Abra Docker Desktop
2. Vá em Settings (ícone de engrenagem)
3. Em "Resources" → "Advanced":
   - CPUs: 4 (recomendado)
   - Memory: 4 GB (mínimo) ou 8 GB (recomendado)
   - Swap: 1 GB
   - Disk image size: 60 GB

4. Em "General":
   - ✅ Start Docker Desktop when you log in
   - ✅ Use WSL 2 based engine

5. Clique em "Apply & Restart"

## Passo 7: Iniciar Infraestrutura WiFiSense

Navegue até a pasta do projeto:

```bash
cd "C:\Users\edyen\Desktop\UpCode\movimento wifi"
```

### Opção 1: Usar Makefile (Recomendado)

```bash
# Ver comandos disponíveis
make help

# Setup inicial (cria .env se não existir)
make setup

# Iniciar infraestrutura (PostgreSQL, Redis, RabbitMQ)
make infra-up

# Verificar status
make ps

# Ver logs
make logs
```

### Opção 2: Docker Compose Direto

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Iniciar apenas infraestrutura
docker-compose up -d postgres redis rabbitmq

# Verificar containers rodando
docker-compose ps

# Ver logs
docker-compose logs -f
```

## Passo 8: Verificar Serviços

### PostgreSQL
```bash
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas -c "\dn"
```

Deve mostrar os 7 schemas:
- auth_schema
- tenant_schema
- device_schema
- license_schema
- event_schema
- notification_schema
- billing_schema

### Redis
```bash
docker exec -it wifisense-redis redis-cli ping
```

Deve retornar: `PONG`

### RabbitMQ
Acesse: http://localhost:15672
- Usuário: `wifisense`
- Senha: `wifisense_password`

## Passo 9: Iniciar Microserviços

### Opção 1: Todos os serviços
```bash
docker-compose up -d
```

### Opção 2: Serviços específicos
```bash
# Apenas auth-service
docker-compose up -d auth-service

# Apenas tenant-service
docker-compose up -d tenant-service
```

## Passo 10: Testar Integração Completa

Execute o script de validação:

```bash
# Tornar executável (Git Bash)
chmod +x scripts/validate-setup.sh
./scripts/validate-setup.sh

# Ou executar diretamente
bash scripts/validate-setup.sh
```

## Comandos Úteis

### Gerenciar Containers
```bash
# Ver containers rodando
docker ps

# Ver todos os containers (incluindo parados)
docker ps -a

# Parar todos os containers
docker-compose down

# Parar e remover volumes (CUIDADO: apaga dados)
docker-compose down -v

# Reiniciar um serviço específico
docker-compose restart auth-service

# Ver logs de um serviço
docker-compose logs -f auth-service
```

### Acessar Container
```bash
# Acessar PostgreSQL
docker exec -it wifisense-postgres psql -U wifisense -d wifisense_saas

# Acessar Redis CLI
docker exec -it wifisense-redis redis-cli

# Acessar bash de um container
docker exec -it wifisense-auth-service bash
```

### Limpar Docker
```bash
# Remover containers parados
docker container prune

# Remover imagens não usadas
docker image prune

# Remover volumes não usados
docker volume prune

# Limpar tudo (CUIDADO)
docker system prune -a --volumes
```

## Solução de Problemas

### Erro: "Docker daemon is not running"
- Abra Docker Desktop
- Aguarde inicializar (ícone da baleia na bandeja)

### Erro: "WSL 2 installation is incomplete"
```powershell
# Atualizar kernel do WSL 2
wsl --update
```

### Erro: "Port already in use"
```bash
# Ver o que está usando a porta
netstat -ano | findstr :5432

# Parar o processo (substitua PID)
taskkill /PID <PID> /F
```

### Containers não iniciam
```bash
# Ver logs de erro
docker-compose logs

# Recriar containers
docker-compose up -d --force-recreate
```

### PostgreSQL não aceita conexões
```bash
# Verificar se está rodando
docker-compose ps postgres

# Ver logs
docker-compose logs postgres

# Reiniciar
docker-compose restart postgres
```

## Próximos Passos

Após instalar o Docker:

1. ✅ Iniciar infraestrutura: `make infra-up`
2. ✅ Verificar schemas: `make db-check`
3. ✅ Testar auth-service: `cd services/auth-service && python test_auth_simple.py`
4. ✅ Testar tenant-service: `cd services/tenant-service && python test_tenant_service.py`
5. ✅ Executar validação completa: `./scripts/validate-setup.sh`

## Recursos Adicionais

- **Documentação Docker:** https://docs.docker.com/
- **Docker Desktop Windows:** https://docs.docker.com/desktop/windows/
- **WSL 2:** https://docs.microsoft.com/pt-br/windows/wsl/
- **Troubleshooting:** https://docs.docker.com/desktop/troubleshoot/overview/

---

**Dúvidas?** Consulte a documentação ou execute `make help` para ver comandos disponíveis.
