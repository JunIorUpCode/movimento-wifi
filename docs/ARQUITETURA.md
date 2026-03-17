# 🏗️ Arquitetura do WiFiSense Local

## Visão Geral

O WiFiSense Local é um sistema de monitoramento de presença e movimento baseado em sinais Wi-Fi, projetado com arquitetura modular e extensível.

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│  Dashboard │ Histórico │ Configurações │ WebSocket Client   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   API REST   │  │  WebSocket   │  │   Services   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│              ┌─────────────────────────┐                    │
│              │   MonitorService        │                    │
│              │   (Loop Assíncrono)     │                    │
│              └────────┬────────────────┘                    │
│                       │                                      │
│         ┌─────────────┼─────────────┐                       │
│         ▼             ▼             ▼                       │
│   ┌─────────┐  ┌──────────┐  ┌──────────┐                 │
│   │ Capture │  │Processing│  │Detection │                 │
│   └─────────┘  └──────────┘  └──────────┘                 │
│         │             │             │                       │
│         └─────────────┴─────────────┘                       │
│                       │                                      │
│                       ▼                                      │
│              ┌─────────────────┐                            │
│              │  SQLite (DB)    │                            │
│              └─────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Camadas do Backend

### 1. Camada de Captura (Capture Layer)

**Responsabilidade**: Aquisição de dados de sinal Wi-Fi

**Arquivos**:
- `capture/base.py` - Interface abstrata `SignalProvider`
- `capture/mock_provider.py` - Gerador de sinais sintéticos
- `capture/rssi_placeholder.py` - Placeholder para RSSI real
- `capture/csi_placeholder.py` - Placeholder para CSI real

**Padrão de Design**: Strategy Pattern

```python
class SignalProvider(ABC):
    @abstractmethod
    async def get_signal(self) -> SignalData:
        """Retorna uma amostra de sinal"""
        pass
```

**Extensibilidade**: Para adicionar novo provider:
1. Crie classe herdando de `SignalProvider`
2. Implemente `get_signal()`, `start()`, `stop()`
3. Registre no `ConfigService`

---

### 2. Camada de Processamento (Processing Layer)

**Responsabilidade**: Transformar sinal bruto em features úteis

**Arquivos**:
- `processing/signal_processor.py`

**Pipeline**:
```
Sinal Bruto → Normalização → Suavização → Extração de Features
```

**Features Extraídas**:
- `rssi_normalized` - RSSI normalizado [0, 1]
- `rssi_smoothed` - RSSI com média móvel
- `signal_energy` - Energia do CSI (soma dos quadrados)
- `signal_variance` - Variância das amplitudes
- `rate_of_change` - Taxa de variação entre amostras
- `instability_score` - Score de instabilidade [0, 1]
- `csi_mean_amplitude` - Amplitude média das subportadoras
- `csi_std_amplitude` - Desvio padrão das amplitudes

**Janela Temporal**: Mantém buffer de 50 amostras para cálculos estatísticos

---

### 3. Camada de Detecção (Detection Layer)

**Responsabilidade**: Classificar eventos com base nas features

**Arquivos**:
- `detection/base.py` - Interface `DetectorBase`
- `detection/heuristic_detector.py` - Detector baseado em regras

**Eventos Detectados**:
- `NO_PRESENCE` - Ambiente vazio
- `PRESENCE_STILL` - Presença parada
- `PRESENCE_MOVING` - Presença em movimento
- `FALL_SUSPECTED` - Possível queda
- `PROLONGED_INACTIVITY` - Inatividade prolongada

**Lógica Heurística**:
```python
if rate_of_change >= fall_threshold:
    return FALL_SUSPECTED
elif signal_energy < presence_threshold:
    return NO_PRESENCE
elif signal_variance >= movement_threshold:
    return PRESENCE_MOVING
elif still_duration >= inactivity_timeout:
    return PROLONGED_INACTIVITY
else:
    return PRESENCE_STILL
```

**Extensibilidade**: Para substituir por ML:
1. Crie classe herdando de `DetectorBase`
2. Implemente `detect(features) -> DetectionResult`
3. Substitua em `MonitorService.__init__()`

---

### 4. Camada de Serviços (Services Layer)

**Responsabilidade**: Lógica de negócio e orquestração

#### MonitorService (Singleton)
- Orquestra o pipeline completo
- Loop assíncrono de monitoramento
- Gerencia conexões WebSocket
- Controla estado do sistema

**Fluxo do Loop**:
```python
while is_running:
    signal = await provider.get_signal()      # 1. Captura
    features = processor.process(signal)      # 2. Processamento
    result = detector.detect(features)        # 3. Detecção
    alert = alert_service.evaluate(result)    # 4. Alertas
    await history_service.save(result)        # 5. Persistência
    await broadcast_ws(result)                # 6. Broadcast
    await asyncio.sleep(interval)
```

#### AlertService
- Avalia eventos críticos
- Gera alertas visuais
- Estrutura pronta para alertas externos

#### ConfigService (Singleton)
- Gerencia configuração em memória
- Converte para `ThresholdConfig` do detector

#### HistoryService
- CRUD de eventos no SQLite
- Queries otimizadas com índices

---

### 5. Camada de API (API Layer)

**Responsabilidade**: Interface HTTP/WebSocket

**Rotas REST**:
```
GET  /api/health              - Health check
GET  /api/status              - Estado atual
GET  /api/events              - Histórico (com filtros)
GET  /api/config              - Configuração
POST /api/config              - Atualizar config
POST /api/simulation/mode     - Trocar modo simulação
POST /api/monitor/start       - Iniciar monitoramento
POST /api/monitor/stop        - Parar monitoramento
```

**WebSocket**:
```
WS /ws/live - Stream de atualizações em tempo real
```

**Payload WebSocket**:
```json
{
  "event_type": "presence_moving",
  "confidence": 0.85,
  "timestamp": 1234567890.123,
  "signal": { "rssi": -45.2, "csi_mean": 5.3 },
  "features": { "signal_energy": 12.5, ... },
  "alert": "⚠️ Possível queda detectada!"
}
```

---

### 6. Camada de Persistência (Database Layer)

**Banco**: SQLite com SQLAlchemy ORM

**Modelo Event**:
```python
class Event(Base):
    id: int
    timestamp: datetime
    event_type: str
    confidence: float
    provider: str
    metadata_json: str
```

**Índices**: `timestamp`, `event_type` para queries rápidas

---

## Frontend (React + TypeScript)

### Arquitetura de Componentes

```
App
├── Header
├── Sidebar
└── Pages
    ├── Dashboard
    │   ├── AlertBanner
    │   ├── StatusCard
    │   ├── PresenceIndicator
    │   ├── ConfidenceScore
    │   ├── MonitorControls
    │   ├── SignalChart (Recharts)
    │   └── EventTimeline
    ├── History
    │   └── EventTable
    └── Settings
        └── ConfigForm
```

### Gerenciamento de Estado (Zustand)

**Store Global**:
```typescript
interface AppState {
  // Status
  isMonitoring: boolean
  currentEvent: EventType
  confidence: number
  
  // Dados
  signalHistory: ChartDataPoint[]
  events: EventRecord[]
  
  // Alertas
  activeAlert: string | null
  
  // Config
  config: AppConfig
  
  // Actions
  setMonitoring(v: boolean): void
  pushLiveUpdate(u: LiveUpdate): void
  ...
}
```

### Comunicação

**REST API**: `services/api.ts` - Wrapper do fetch
**WebSocket**: `hooks/useWebSocket.ts` - Auto-reconnect

---

## Fluxo de Dados Completo

### 1. Inicialização
```
User → Frontend → POST /api/monitor/start
                → Backend cria loop assíncrono
                → Provider.start()
                → Processor.reset()
                → Detector.reset()
```

### 2. Monitoramento (Loop)
```
Provider → SignalData
         ↓
Processor → ProcessedFeatures
          ↓
Detector → DetectionResult
         ↓
AlertService → Alert?
             ↓
HistoryService → SQLite
               ↓
WebSocket → Frontend (tempo real)
```

### 3. Atualização Frontend
```
WebSocket → useWebSocket hook
          → useStore.pushLiveUpdate()
          → Componentes re-renderizam
          → Gráficos atualizam
          → Alertas aparecem
```

---

## Padrões de Design Utilizados

### 1. Strategy Pattern
- `SignalProvider` - Diferentes estratégias de captura
- `DetectorBase` - Diferentes estratégias de detecção

### 2. Singleton Pattern
- `MonitorService` - Instância única do orquestrador
- `ConfigService` - Configuração global
- `AlertService` - Gerenciador de alertas

### 3. Observer Pattern
- WebSocket - Observadores recebem atualizações
- Zustand - Componentes observam mudanças de estado

### 4. Pipeline Pattern
- Captura → Processamento → Detecção → Persistência

### 5. Repository Pattern
- `HistoryService` - Abstração do acesso ao banco

---

## Decisões Arquiteturais

### Por que FastAPI?
- Async/await nativo (essencial para WebSocket + loop)
- Validação automática com Pydantic
- Documentação automática (Swagger)
- Performance superior

### Por que SQLite?
- Zero configuração
- Arquivo único portável
- Suficiente para uso local
- Fácil backup

### Por que Zustand?
- API simples e direta
- Sem boilerplate
- TypeScript first-class
- Performance excelente

### Por que Recharts?
- Componentes declarativos
- Animações suaves
- Responsivo
- Customizável

---

## Extensibilidade

### Adicionar Novo Provider
```python
# 1. Criar classe
class MyProvider(SignalProvider):
    async def get_signal(self) -> SignalData:
        # Implementação
        pass

# 2. Registrar
monitor_service._provider = MyProvider()
```

### Adicionar Novo Detector
```python
# 1. Criar classe
class MLDetector(DetectorBase):
    def __init__(self):
        self.model = load_model('model.pkl')
    
    def detect(self, features: ProcessedFeatures) -> DetectionResult:
        prediction = self.model.predict(features)
        return DetectionResult(...)

# 2. Substituir
monitor_service._detector = MLDetector()
```

### Adicionar Nova Feature
```python
# 1. Adicionar em ProcessedFeatures
@dataclass
class ProcessedFeatures:
    ...
    my_new_feature: float

# 2. Calcular em SignalProcessor.process()
def process(self, signal: SignalData) -> ProcessedFeatures:
    ...
    my_new_feature = self._calculate_new_feature(signal)
    return ProcessedFeatures(..., my_new_feature=my_new_feature)
```

### Adicionar Alerta Externo
```python
# Em AlertService.evaluate()
async def evaluate(self, event_type, confidence):
    alert = self._create_alert(event_type, confidence)
    if alert:
        await self._send_whatsapp(alert)
        await self._send_sms(alert)
        await self._send_push(alert)
    return alert
```

---

## Performance

### Backend
- Loop assíncrono não bloqueante
- Processamento em memória (buffers circulares)
- Persistência apenas em mudanças de estado
- WebSocket broadcast eficiente

### Frontend
- Componentes React otimizados
- Zustand com seletores granulares
- Gráficos com animações controladas
- Polling apenas para histórico (3s)

### Banco de Dados
- Índices em campos de busca
- Queries limitadas (LIMIT)
- Sem joins complexos
- Limpeza automática de histórico antigo (futuro)

---

## Segurança

### Backend
- CORS configurado para localhost
- Validação de entrada com Pydantic
- Sem autenticação (uso local)
- Preparado para adicionar JWT

### Frontend
- Proxy Vite para evitar CORS
- Sanitização de inputs
- Tratamento de erros
- Reconexão automática WebSocket

---

## Testes (Futuro)

### Backend
```python
# tests/test_processor.py
def test_signal_normalization():
    processor = SignalProcessor()
    signal = SignalData(rssi=-50, ...)
    features = processor.process(signal)
    assert 0 <= features.rssi_normalized <= 1

# tests/test_detector.py
def test_fall_detection():
    detector = HeuristicDetector()
    features = ProcessedFeatures(rate_of_change=15, ...)
    result = detector.detect(features)
    assert result.event_type == EventType.FALL_SUSPECTED
```

### Frontend
```typescript
// tests/useStore.test.ts
test('pushLiveUpdate updates state', () => {
  const { result } = renderHook(() => useStore())
  act(() => {
    result.current.pushLiveUpdate(mockUpdate)
  })
  expect(result.current.currentEvent).toBe('presence_moving')
})
```

---

## Monitoramento e Logs

### Backend
```python
# Logs estruturados
logger.info("Monitor started", extra={"provider": "mock"})
logger.warning("High instability", extra={"score": 0.95})
logger.error("Provider failed", exc_info=True)
```

### Frontend
```typescript
// Console logs para debug
console.log('[WS] Conectado')
console.error('Erro ao carregar eventos:', error)
```

---

## Deployment (Futuro)

### Opção 1: Executável Standalone
- PyInstaller (backend)
- Electron (frontend + backend)
- Instalador Windows

### Opção 2: Docker
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
```

### Opção 3: Systemd Service (Linux)
```ini
[Unit]
Description=WiFiSense Backend

[Service]
ExecStart=/path/to/venv/bin/uvicorn app.main:app
WorkingDirectory=/path/to/backend
Restart=always

[Install]
WantedBy=multi-user.target
```

---

**Arquitetura projetada para ser simples, extensível e profissional.**
