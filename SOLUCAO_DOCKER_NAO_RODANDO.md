# 🔧 Solução: Docker não está rodando

## Erro Identificado

```
failed to connect to the docker API at npipe:////./pipe/docker_engine
The system cannot find the file specified.
```

**Causa:** O Docker Desktop não está rodando ou não foi iniciado corretamente.

## ✅ Solução Passo a Passo

### Passo 1: Verificar se Docker Desktop está instalado

1. Pressione `Win + S` e procure por "Docker Desktop"
2. Se não encontrar, você precisa instalar primeiro

**Se não estiver instalado:**
- Baixe em: https://www.docker.com/products/docker-desktop/
- Execute o instalador
- Reinicie o computador após a instalação

### Passo 2: Iniciar Docker Desktop

**Opção 1: Menu Iniciar**
1. Pressione `Win + S`
2. Digite "Docker Desktop"
3. Clique em "Docker Desktop" para abrir
4. Aguarde o ícone da baleia aparecer na bandeja do sistema (canto inferior direito)

**Opção 2: Atalho**
- Procure o ícone do Docker Desktop na área de trabalho
- Clique duas vezes para abrir

**Opção 3: Linha de comando**
```powershell
# Abrir como Administrador
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### Passo 3: Aguardar Inicialização

1. Após abrir o Docker Desktop, aguarde 30-60 segundos
2. Observe o ícone da baleia na bandeja do sistema:
   - 🐋 **Animado (piscando):** Docker está iniciando
   - 🐋 **Parado (estático):** Docker está pronto
3. Quando o ícone parar de piscar, o Docker está pronto

### Passo 4: Verificar Status

Abra PowerShell ou CMD e execute:

```powershell
# Verificar versão
docker --version

# Testar Docker
docker run hello-world
```

**Resultado esperado:**
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

## 🔍 Problemas Comuns

### Problema 1: Docker Desktop não abre

**Solução:**
```powershell
# 1. Verificar se está rodando
Get-Process "Docker Desktop" -ErrorAction SilentlyContinue

# 2. Se não estiver, iniciar
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 3. Aguardar 60 segundos
Start-Sleep -Seconds 60

# 4. Testar
docker --version
```

### Problema 2: "WSL 2 installation is incomplete"

**Solução:**
```powershell
# Abrir PowerShell como Administrador
# Executar:
wsl --install
wsl --update

# Reiniciar o computador
Restart-Computer
```

### Problema 3: "Hardware assisted virtualization is not enabled"

**Solução:**
1. Reiniciar o computador
2. Entrar na BIOS/UEFI (geralmente F2, F10, Del ou Esc durante boot)
3. Procurar por:
   - Intel: "Intel VT-x" ou "Virtualization Technology"
   - AMD: "AMD-V" ou "SVM Mode"
4. Habilitar a opção
5. Salvar e sair (F10)

### Problema 4: Docker Desktop instalado mas não aparece

**Solução:**
```powershell
# Reinstalar Docker Desktop
# 1. Desinstalar
winget uninstall Docker.DockerDesktop

# 2. Baixar nova versão
# Ir para: https://www.docker.com/products/docker-desktop/

# 3. Instalar novamente
# Executar o instalador baixado

# 4. Reiniciar
Restart-Computer
```

### Problema 5: "Access denied" ao executar docker

**Solução:**
```powershell
# Adicionar usuário ao grupo docker-users
net localgroup docker-users "SEU_USUARIO" /add

# Fazer logout e login novamente
# Ou reiniciar o computador
```

## 🚀 Após Docker Iniciar

Quando o Docker estiver rodando, execute:

```bash
# 1. Navegar para o projeto
cd "C:\Users\edyen\Desktop\UpCode\movimento wifi"

# 2. Iniciar infraestrutura
make infra-up

# Ou
docker-compose up -d postgres redis rabbitmq

# 3. Verificar containers
docker ps

# 4. Verificar health
make infra-health
```

## 📋 Checklist de Validação

- [ ] Docker Desktop instalado
- [ ] Docker Desktop aberto e rodando
- [ ] Ícone da baleia visível na bandeja (não piscando)
- [ ] `docker --version` funciona
- [ ] `docker run hello-world` funciona
- [ ] Containers podem ser iniciados

## 🔄 Comandos Úteis

### Verificar se Docker está rodando
```powershell
# Windows
Get-Process "Docker Desktop" -ErrorAction SilentlyContinue

# Ou
docker info
```

### Reiniciar Docker Desktop
```powershell
# Parar
Stop-Process -Name "Docker Desktop" -Force

# Aguardar 5 segundos
Start-Sleep -Seconds 5

# Iniciar
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Aguardar inicializar
Start-Sleep -Seconds 60
```

### Ver logs do Docker Desktop
1. Abrir Docker Desktop
2. Clicar no ícone de engrenagem (Settings)
3. Ir em "Troubleshoot"
4. Clicar em "View logs"

## 📞 Suporte Adicional

Se nenhuma solução funcionar:

1. **Desinstalar completamente:**
   ```powershell
   # Desinstalar
   winget uninstall Docker.DockerDesktop
   
   # Remover dados
   Remove-Item -Recurse -Force "$env:APPDATA\Docker"
   Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Docker"
   ```

2. **Reinstalar:**
   - Baixar versão mais recente
   - Instalar como Administrador
   - Reiniciar o computador

3. **Verificar requisitos do sistema:**
   - Windows 10 versão 2004 ou superior
   - WSL 2 instalado
   - Virtualização habilitada na BIOS
   - Mínimo 4 GB de RAM disponível

## ✅ Próximo Passo

Após o Docker iniciar com sucesso:

```bash
# Testar hello-world
docker run hello-world

# Se funcionar, iniciar infraestrutura WiFiSense
cd "C:\Users\edyen\Desktop\UpCode\movimento wifi"
make infra-up
make infra-health
```

---

**Dica:** Sempre mantenha o Docker Desktop aberto enquanto estiver desenvolvendo. Você pode minimizá-lo, mas não feche completamente.
