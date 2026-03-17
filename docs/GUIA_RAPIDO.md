# 🚀 Guia Rápido - WiFiSense Local

## Instalação Rápida (Windows)

### Opção 1: Scripts Automáticos (Recomendado)

1. **Backend**: Clique duas vezes em `start_backend.bat`
2. **Frontend**: Clique duas vezes em `start_frontend.bat`
3. Abra o navegador em `http://localhost:5173`

### Opção 2: Manual

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## ✅ Checklist de Funcionamento

Após iniciar, verifique:

- [ ] Backend rodando em `http://localhost:8000`
- [ ] Frontend rodando em `http://localhost:5173`
- [ ] API respondendo em `http://localhost:8000/api/health`
- [ ] Dashboard carregando sem erros
- [ ] WebSocket conectado (veja console do navegador)

---

## 🎮 Primeiros Passos

1. **Acesse o Dashboard**: `http://localhost:5173`

2. **Inicie o Monitoramento**: Clique em "Iniciar Monitoramento"

3. **Teste os Modos de Simulação**:
   - **Ambiente Vazio**: Sem presença detectada
   - **Pessoa Parada**: Presença com micro-movimentos
   - **Pessoa Andando**: Movimento ativo
   - **Queda Simulada**: Simula evento de queda
   - **Imobilidade Pós-Queda**: Inatividade prolongada
   - **Aleatório**: Alterna entre modos

4. **Explore as Páginas**:
   - **Dashboard**: Monitoramento em tempo real
   - **Histórico**: Eventos salvos no banco
   - **Configurações**: Ajuste sensibilidade e limiares

---

## 🔧 Configurações Importantes

### Sensibilidade de Movimento
- **Padrão**: 2.0
- **Menor valor** = mais sensível (detecta movimentos sutis)
- **Maior valor** = menos sensível (ignora micro-movimentos)

### Limiar de Queda
- **Padrão**: 12.0
- **Menor valor** = detecta quedas mais facilmente
- **Maior valor** = requer mudança mais brusca

### Tempo de Inatividade
- **Padrão**: 30 segundos
- Define quanto tempo sem movimento para alertar inatividade prolongada

### Intervalo de Amostragem
- **Padrão**: 0.5 segundos
- **Menor valor** = mais amostras por segundo (mais preciso, mais CPU)
- **Maior valor** = menos amostras (menos preciso, menos CPU)

---

## 📊 Entendendo o Dashboard

### Cards Superiores
1. **Estado Atual**: Mostra o evento detectado no momento
2. **Indicador de Presença**: Animação visual do estado
3. **Score de Confiança**: Nível de certeza da detecção (0-100%)

### Controles
- **Iniciar/Parar Monitoramento**: Liga/desliga o sistema
- **Modos de Simulação**: Troca o comportamento do sinal simulado

### Gráficos
- **Sinal em Tempo Real**: RSSI, Energia e Variância ao longo do tempo
- **Eventos Recentes**: Timeline dos últimos 15 eventos

---

## 🐛 Solução de Problemas

### Backend não inicia
```bash
# Verifique a versão do Python (precisa ser 3.10+)
python --version

# Reinstale as dependências
cd backend
pip install -r requirements.txt --force-reinstall
```

### Frontend não inicia
```bash
# Verifique a versão do Node (precisa ser 18+)
node --version

# Limpe cache e reinstale
cd frontend
rmdir /s /q node_modules
del package-lock.json
npm install
```

### WebSocket não conecta
- Verifique se o backend está rodando
- Abra o console do navegador (F12) e veja erros
- Certifique-se de que não há firewall bloqueando a porta 8000

### Banco de dados com erro
```bash
# Delete e recrie o banco
cd backend
del wifisense.db
# Reinicie o backend - ele criará um novo banco
```

---

## 📁 Estrutura do Projeto

```
wifi-sense-local/
├── backend/
│   ├── app/
│   │   ├── api/          # Rotas REST + WebSocket
│   │   ├── capture/      # Providers de sinal (mock + placeholders)
│   │   ├── processing/   # Processamento de sinal
│   │   ├── detection/    # Detecção de eventos
│   │   ├── services/     # Lógica de negócio
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── db/           # Configuração do banco
│   ├── requirements.txt
│   └── wifisense.db      # SQLite (criado automaticamente)
│
├── frontend/
│   ├── src/
│   │   ├── components/   # Componentes React
│   │   ├── pages/        # Páginas (Dashboard, History, Settings)
│   │   ├── hooks/        # Custom hooks (WebSocket)
│   │   ├── services/     # API client
│   │   ├── store/        # Zustand state
│   │   └── types/        # TypeScript types
│   ├── package.json
│   └── vite.config.ts
│
├── start_backend.bat     # Script de inicialização do backend
├── start_frontend.bat    # Script de inicialização do frontend
├── README.md             # Documentação completa
└── GUIA_RAPIDO.md        # Este arquivo
```

---

## 🔮 Próximos Passos

### Integração com Hardware Real

#### 1. Captura RSSI
Edite `backend/app/capture/rssi_placeholder.py`:
```python
async def get_signal(self) -> SignalData:
    # Substitua por código real de captura RSSI
    # Exemplo com scapy, pyshark ou SDK do adaptador
    rssi = await self._read_rssi_from_adapter()
    return SignalData(rssi=rssi, csi_amplitude=[], ...)
```

#### 2. Captura CSI
Edite `backend/app/capture/csi_placeholder.py`:
```python
async def get_signal(self) -> SignalData:
    # Substitua por código real de captura CSI
    # Hardware: Intel 5300, ESP32-S3, Atheros
    csi_data = await self._read_csi_from_hardware()
    return SignalData(rssi=..., csi_amplitude=csi_data, ...)
```

#### 3. Trocar Provider Ativo
Vá em **Configurações** → **Provider Ativo** → Selecione `rssi` ou `csi`

### Machine Learning

1. Colete dados reais usando o sistema atual
2. Exporte eventos do banco SQLite
3. Treine um modelo (Random Forest, LSTM, CNN)
4. Crie nova classe implementando `DetectorBase`
5. Substitua `HeuristicDetector` em `MonitorService`

### Alertas Externos

Edite `backend/app/services/alert_service.py`:
```python
async def send_external_alert(self, alert: Alert):
    # WhatsApp Business API
    # Twilio SMS
    # Firebase Push Notification
    pass
```

---

## 📞 Suporte

- **Documentação Completa**: Veja `README.md`
- **Código Fonte**: Todos os arquivos estão comentados
- **Arquitetura**: Sistema modular e extensível

---

**Desenvolvido com ❤️ para monitoramento local de presença via Wi-Fi**
