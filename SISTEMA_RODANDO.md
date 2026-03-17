# 🎉 SISTEMA RODANDO COM SUCESSO!

## ✅ Status Atual

### Backend - ✅ RODANDO
- **URL**: http://localhost:8000
- **Status**: Online
- **Porta**: 8000
- **Processo**: Uvicorn rodando em background

### Frontend - ✅ RODANDO
- **URL**: http://localhost:5173
- **Status**: Online
- **Porta**: 5173
- **Processo**: Vite dev server rodando em background

### Banco de Dados - ✅ INICIALIZADO
- **Arquivo**: backend/wifisense.db
- **Status**: Criado e pronto para uso
- **Tipo**: SQLite

---

## 🚀 ACESSE AGORA

### 1. Abra o Dashboard
```
http://localhost:5173
```

### 2. Teste a API
```
http://localhost:8000/docs
```
(Documentação interativa Swagger)

### 3. Health Check
```
http://localhost:8000/api/health
```

---

## 🎮 COMO USAR

### Passo 1: Iniciar Monitoramento
1. Acesse http://localhost:5173
2. Clique no botão verde **"Iniciar Monitoramento"**
3. Aguarde o sistema começar a capturar dados

### Passo 2: Testar Modos de Simulação
Experimente os diferentes modos:

- **🏠 Ambiente Vazio**: Sem presença detectada
- **🧍 Pessoa Parada**: Presença com micro-movimentos (respiração)
- **🚶 Pessoa Andando**: Movimento ativo detectado
- **🤕 Queda Simulada**: Simula evento de queda brusca
- **😴 Imobilidade Pós-Queda**: Inatividade prolongada
- **🎲 Aleatório**: Alterna entre todos os modos

### Passo 3: Observar Dashboard
Você verá em tempo real:
- ✅ Estado atual (card superior esquerdo)
- ✅ Indicador visual animado (centro)
- ✅ Score de confiança (direita)
- ✅ Gráfico de sinal (RSSI, energia, variância)
- ✅ Timeline de eventos recentes

### Passo 4: Explorar Outras Páginas

**📊 Histórico**
- Clique em "Histórico" na sidebar
- Veja todos os eventos salvos no banco
- Filtre por tipo de evento
- Atualize com o botão de refresh

**⚙️ Configurações**
- Clique em "Configurações" na sidebar
- Ajuste sensibilidade de movimento
- Ajuste limiar de queda
- Configure tempo de inatividade
- Altere intervalo de amostragem
- Clique em "Salvar Configurações"

---

## 📊 ENDPOINTS DA API

### REST API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/health` | Health check do sistema |
| GET | `/api/status` | Estado atual do monitoramento |
| GET | `/api/events` | Histórico de eventos |
| GET | `/api/config` | Configuração atual |
| POST | `/api/config` | Atualizar configuração |
| POST | `/api/simulation/mode` | Trocar modo de simulação |
| POST | `/api/monitor/start` | Iniciar monitoramento |
| POST | `/api/monitor/stop` | Parar monitoramento |

### WebSocket

| Endpoint | Descrição |
|----------|-----------|
| `ws://localhost:8000/ws/live` | Stream de dados em tempo real |

---

## 🧪 TESTES RÁPIDOS

### Teste 1: Detecção de Movimento
1. Inicie o monitoramento
2. Selecione modo "Pessoa Andando"
3. Observe o card mudar para "Presença (Movendo)" em verde
4. Veja o gráfico com variações amplas

### Teste 2: Detecção de Queda
1. Selecione modo "Queda Simulada"
2. Observe o alerta vermelho aparecer no topo
3. Veja o card mudar para "⚠️ Queda Suspeita"
4. Verifique o pico no gráfico

### Teste 3: Inatividade Prolongada
1. Selecione modo "Imobilidade Pós-Queda"
2. Aguarde 30 segundos (tempo padrão)
3. Observe o alerta amarelo de inatividade
4. Veja o card mudar para "⏳ Inatividade Prolongada"

### Teste 4: Histórico
1. Deixe o sistema rodar por alguns minutos
2. Vá para página "Histórico"
3. Veja todos os eventos salvos
4. Filtre por "Queda Suspeita"

### Teste 5: Configurações
1. Vá para "Configurações"
2. Reduza "Sensibilidade de Movimento" para 1.0
3. Clique em "Salvar Configurações"
4. Volte ao Dashboard
5. Observe que agora detecta movimentos mais sutis

---

## 🔍 MONITORAMENTO DO SISTEMA

### Ver Logs do Backend
Os logs aparecem no terminal onde o backend foi iniciado:
```
[OK] WiFiSense Local - Backend iniciado
[OK] Banco de dados SQLite inicializado
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Ver Logs do Frontend
Os logs aparecem no terminal onde o frontend foi iniciado:
```
VITE v6.4.1 ready in 1621 ms
➜  Local:   http://localhost:5173/
```

### Ver Logs do WebSocket (Browser)
1. Abra o DevTools (F12)
2. Vá para aba "Console"
3. Veja mensagens como:
```
[WS] Conectado
```

---

## 🛑 PARAR O SISTEMA

### Opção 1: Fechar Terminais
- Feche os terminais onde backend e frontend estão rodando

### Opção 2: Ctrl+C
- Pressione Ctrl+C em cada terminal

### Opção 3: Pelo Dashboard
- Clique em "Parar Monitoramento" (para o loop, mas não o servidor)

---

## 📁 ARQUIVOS GERADOS

### Banco de Dados
```
backend/wifisense.db
```
Contém todos os eventos detectados. Você pode:
- Abrir com DB Browser for SQLite
- Fazer backup copiando o arquivo
- Deletar para resetar histórico

### Logs
Os logs aparecem apenas nos terminais (não são salvos em arquivo por padrão).

---

## 🔧 TROUBLESHOOTING

### Backend não responde
```bash
# Verifique se está rodando
curl http://localhost:8000/api/health

# Se não responder, reinicie
# Feche o terminal e execute novamente:
start_backend.bat
```

### Frontend não carrega
```bash
# Verifique se está rodando
curl http://localhost:5173

# Se não responder, reinicie
# Feche o terminal e execute novamente:
start_frontend.bat
```

### WebSocket não conecta
1. Abra DevTools (F12)
2. Vá para aba "Console"
3. Veja se há erros de conexão
4. Verifique se backend está rodando
5. Recarregue a página (F5)

### Gráfico não atualiza
1. Verifique se monitoramento está iniciado
2. Veja se há erros no console (F12)
3. Recarregue a página (F5)

### Eventos não aparecem no histórico
1. Verifique se monitoramento está rodando
2. Aguarde alguns segundos (eventos são salvos em mudanças de estado)
3. Clique no botão de refresh
4. Verifique se arquivo wifisense.db existe

---

## 📊 MÉTRICAS EM TEMPO REAL

Enquanto o sistema roda, você pode ver:

### No Dashboard
- **Taxa de atualização**: ~2 Hz (0.5s por amostra)
- **Pontos no gráfico**: Últimos 60 pontos
- **Eventos na timeline**: Últimos 15 eventos

### No Banco
- **Eventos salvos**: Apenas mudanças de estado
- **Tamanho do banco**: Cresce ~1KB por 100 eventos

---

## 🎯 PRÓXIMOS PASSOS

### 1. Explore o Sistema
- Teste todos os modos de simulação
- Ajuste as configurações
- Observe como os limiares afetam a detecção

### 2. Analise os Dados
- Veja o histórico de eventos
- Observe padrões no gráfico
- Entenda as features extraídas

### 3. Prepare para Hardware Real
- Leia `INTEGRACAO_HARDWARE.md`
- Escolha seu hardware (RSSI ou CSI)
- Planeje a integração

### 4. Considere Machine Learning
- Colete dados reais
- Treine um modelo
- Substitua o detector heurístico

---

## 🎉 PARABÉNS!

Você tem um sistema completo de monitoramento de presença via Wi-Fi rodando localmente!

**O que você pode fazer agora:**
- ✅ Monitorar presença em tempo real
- ✅ Detectar movimento e quedas
- ✅ Visualizar dados em gráficos
- ✅ Salvar histórico de eventos
- ✅ Ajustar configurações dinamicamente
- ✅ Preparar para integração com hardware real

---

**Sistema desenvolvido com ❤️ e pronto para evoluir!**

**Documentação completa**: Veja README.md, GUIA_RAPIDO.md, ARQUITETURA.md
