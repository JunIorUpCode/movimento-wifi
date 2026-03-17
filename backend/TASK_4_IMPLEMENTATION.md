# Task 4: Sistema de Métricas de Performance - Implementação Completa

## Resumo

Implementação completa do sistema de métricas de performance para o WiFiSense Local, incluindo coleta, persistência e análise de métricas de tempo e recursos do sistema.

## Requisitos Atendidos

- **26.1**: Coleta de métricas (tempo de captura, processamento, detecção, latência total)
- **26.2**: Cálculo de estatísticas (média, p95, p99)
- **26.4**: Persistência de métricas no banco de dados
- **26.6**: Warning para latência >500ms

## Componentes Implementados

### 1. PerformanceMetrics Dataclass

**Arquivo**: `backend/app/services/performance_service.py`

```python
@dataclass
class PerformanceMetrics:
    """Métricas de performance de uma iteração do pipeline."""
    
    capture_time_ms: float
    processing_time_ms: float
    detection_time_ms: float
    total_latency_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: float = 0.0
```

**Características**:
- Armazena métricas de tempo para cada etapa do pipeline
- Inclui métricas de recursos (memória e CPU)
- Timestamp automático se não fornecido

### 2. PerformanceStats Dataclass

```python
@dataclass
class PerformanceStats:
    """Estatísticas agregadas de performance."""
    
    mean_capture_ms: float
    mean_processing_ms: float
    mean_detection_ms: float
    mean_total_latency_ms: float
    
    p95_capture_ms: float
    p95_processing_ms: float
    p95_detection_ms: float
    p95_total_latency_ms: float
    
    p99_capture_ms: float
    p99_processing_ms: float
    p99_detection_ms: float
    p99_total_latency_ms: float
    
    max_capture_ms: float
    max_processing_ms: float
    max_detection_ms: float
    max_total_latency_ms: float
    
    mean_memory_mb: float
    mean_cpu_percent: float
    
    sample_count: int
    period_start: datetime
    period_end: datetime
```

**Características**:
- Estatísticas completas para análise de performance
- Inclui média, p95, p99 e máximo para cada métrica
- Metadados do período analisado

### 3. PerformanceService

**Arquivo**: `backend/app/services/performance_service.py`

Serviço singleton responsável por:

#### 3.1 Coleta de Recursos

```python
def get_current_resources(self) -> tuple[float, float]:
    """Obtém uso atual de recursos do sistema."""
    memory_mb = self._process.memory_info().rss / (1024 * 1024)
    cpu_percent = self._process.cpu_percent(interval=0.01)
    return memory_mb, cpu_percent
```

- Usa `psutil` para coletar métricas do processo
- Retorna memória em MB e CPU em percentual

#### 3.2 Gravação de Métricas

```python
async def record_metrics(self, metrics: PerformanceMetrics) -> None:
    """Registra métricas de performance."""
    # Adiciona ao buffer
    self._metrics_buffer.append(metrics)
    
    # Verifica latência alta
    if metrics.total_latency_ms > self._high_latency_threshold_ms:
        self._high_latency_count += 1
        logger.warning(f"High latency detected: {metrics.total_latency_ms:.2f}ms", ...)
    
    # Persiste quando buffer está cheio
    if len(self._metrics_buffer) >= self._buffer_size:
        await self._flush_buffer()
```

**Características**:
- Buffer de 100 métricas antes de persistir (configurável)
- Warning automático para latência >500ms (Requisito 26.6)
- Flush automático quando buffer está cheio

#### 3.3 Persistência

```python
async def _flush_buffer(self) -> None:
    """Persiste métricas do buffer no banco de dados."""
    async with async_session() as db:
        db_metrics = [
            PerformanceMetric(
                timestamp=datetime.fromtimestamp(m.timestamp),
                capture_time_ms=m.capture_time_ms,
                processing_time_ms=m.processing_time_ms,
                detection_time_ms=m.detection_time_ms,
                total_latency_ms=m.total_latency_ms,
                memory_usage_mb=m.memory_usage_mb,
                cpu_usage_percent=m.cpu_usage_percent
            )
            for m in self._metrics_buffer
        ]
        
        db.add_all(db_metrics)
        await db.commit()
```

**Características**:
- Persistência em lote para eficiência
- Usa modelo `PerformanceMetric` do SQLAlchemy
- Logging estruturado de operações

#### 3.4 Cálculo de Estatísticas

```python
async def get_statistics(self, hours: int = 24) -> Optional[PerformanceStats]:
    """Calcula estatísticas de performance para um período."""
    # Busca métricas do período
    # Calcula média, p95, p99, máximo
    # Retorna PerformanceStats
```

**Características**:
- Análise configurável por período (padrão: 24 horas)
- Cálculo de média, p95, p99 e máximo (Requisito 26.2)
- Retorna None se não houver dados

#### 3.5 Limpeza de Dados Antigos

```python
async def cleanup_old_metrics(self, days: int = 7) -> int:
    """Remove métricas antigas do banco de dados."""
```

**Características**:
- Remove métricas com mais de N dias (padrão: 7)
- Retorna número de registros removidos
- Logging de operação

### 4. Integração com MonitorService

**Arquivo**: `backend/app/services/monitor_service.py`

Modificações no loop principal:

```python
async def _monitor_loop(self) -> None:
    """Loop principal do monitoramento."""
    while self._is_running:
        # Inicia medição de performance
        loop_start = time.time()

        # 1. Captura
        capture_start = time.time()
        signal = await self._provider.get_signal()
        capture_time = (time.time() - capture_start) * 1000  # ms
        
        # 2. Processamento
        processing_start = time.time()
        features = self._processor.process(signal)
        processing_time = (time.time() - processing_start) * 1000  # ms
        
        # 3. Detecção
        detection_start = time.time()
        result = self._detector.detect(features)
        detection_time = (time.time() - detection_start) * 1000  # ms
        
        # ... resto do pipeline ...
        
        # 8. Coleta de métricas de performance
        total_latency = (time.time() - loop_start) * 1000  # ms
        memory_mb, cpu_percent = self._performance_service.get_current_resources()
        
        metrics = PerformanceMetrics(
            capture_time_ms=capture_time,
            processing_time_ms=processing_time,
            detection_time_ms=detection_time,
            total_latency_ms=total_latency,
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent,
            timestamp=signal.timestamp
        )
        
        await self._performance_service.record_metrics(metrics)
```

**Características**:
- Medição precisa de cada etapa do pipeline
- Coleta de recursos do sistema
- Gravação assíncrona sem bloquear o loop

### 5. Modelo de Dados

**Arquivo**: `backend/app/models/models.py`

```python
class PerformanceMetric(Base):
    """Métricas de performance do sistema."""
    
    __tablename__ = "performance_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    capture_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    detection_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    total_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    memory_usage_mb: Mapped[float] = mapped_column(Float, nullable=False)
    cpu_usage_percent: Mapped[float] = mapped_column(Float, nullable=False)
```

**Características**:
- Índice em timestamp para queries eficientes
- Todos os campos obrigatórios
- Tipos apropriados (Float para métricas)

## Dependências Adicionadas

**Arquivo**: `backend/requirements.txt`

```
psutil>=5.9.0
```

- `psutil`: Biblioteca para coleta de métricas de sistema (CPU, memória)

## Testes

### Teste de Integração

**Arquivo**: `backend/test_task4_simple.py`

Testa:
1. ✅ Coleta de métricas
2. ✅ Persistência no banco
3. ✅ Cálculo de estatísticas (média, p95, p99)
4. ✅ Warning para latência >500ms
5. ✅ Coleta de recursos do sistema

**Execução**:
```bash
python backend/test_task4_simple.py
```

**Resultado**:
```
✅ TODOS OS TESTES PASSARAM!

Resumo da Implementação:
  ✓ PerformanceMetrics dataclass criada
  ✓ PerformanceService implementado
  ✓ Coleta de métricas funcionando
  ✓ Persistência no banco funcionando
  ✓ Cálculo de estatísticas (média, p95, p99) funcionando
  ✓ Warning para latência >500ms funcionando
  ✓ Integração com MonitorService completa

Requisitos atendidos: 26.1, 26.2, 26.4, 26.6
```

## Uso

### Coleta Automática

As métricas são coletadas automaticamente pelo `MonitorService` a cada iteração do loop de monitoramento.

### Consulta de Estatísticas

```python
from app.services.performance_service import performance_service

# Estatísticas das últimas 24 horas
stats = await performance_service.get_statistics(hours=24)

print(f"Latência média: {stats.mean_total_latency_ms:.2f}ms")
print(f"Latência p95: {stats.p95_total_latency_ms:.2f}ms")
print(f"Latência p99: {stats.p99_total_latency_ms:.2f}ms")
print(f"Memória média: {stats.mean_memory_mb:.2f}MB")
```

### Limpeza de Dados Antigos

```python
# Remove métricas com mais de 7 dias
count = await performance_service.cleanup_old_metrics(days=7)
print(f"Removidas {count} métricas antigas")
```

## Logging

O sistema gera logs estruturados para:

1. **Alta Latência** (WARNING):
```json
{
  "timestamp": "2026-03-14T13:25:02Z",
  "level": "WARNING",
  "component": "app.services.performance_service",
  "message": "High latency detected: 550.00ms",
  "context": {
    "capture_ms": 200.0,
    "processing_ms": 150.0,
    "detection_ms": 200.0,
    "total_ms": 550.0,
    "memory_mb": 150.0,
    "cpu_percent": 25.0
  }
}
```

2. **Persistência** (INFO):
```json
{
  "timestamp": "2026-03-14T13:25:02Z",
  "level": "INFO",
  "component": "app.services.performance_service",
  "message": "Persisted 100 performance metrics",
  "context": {
    "count": 100,
    "high_latency_count": 5
  }
}
```

## Próximos Passos

Para futuras melhorias:

1. **API REST**: Adicionar endpoints para consultar métricas
   - `GET /api/metrics/performance?hours=24`
   - `GET /api/metrics/current`

2. **Prometheus**: Expor métricas em formato Prometheus
   - `GET /metrics`

3. **Alertas**: Integrar com sistema de notificações
   - Alertar quando latência média > threshold
   - Alertar quando memória > threshold

4. **Dashboard**: Visualização em tempo real no frontend
   - Gráficos de latência
   - Gráficos de recursos

## Conclusão

A Task 4 foi implementada com sucesso, atendendo todos os requisitos especificados:

- ✅ **26.1**: Coleta de métricas de tempo e recursos
- ✅ **26.2**: Cálculo de estatísticas (média, p95, p99, máximo)
- ✅ **26.4**: Persistência no banco de dados
- ✅ **26.6**: Warning para latência >500ms

O sistema está pronto para monitorar a performance do WiFiSense Local em produção e identificar gargalos de performance.
