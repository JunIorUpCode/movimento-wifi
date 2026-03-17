# Sistema de Auto-Detecção de Hardware

## 📋 Visão Geral

O WiFiSense agora possui um sistema inteligente de auto-detecção que identifica automaticamente qual hardware está disponível e seleciona o melhor provider de captura.

## 🎯 Ordem de Prioridade

O sistema tenta os providers nesta ordem:

1. **CSI Provider** (melhor qualidade)
   - Requer hardware específico: Intel 5300, Atheros CSI Tool, ESP32-S3
   - Captura informações detalhadas do canal (amplitude, fase)
   - Ideal para plano PREMIUM

2. **RSSI Windows Provider**
   - Funciona em qualquer Windows com placa Wi-Fi
   - Usa comando nativo `netsh`
   - Não requer instalação adicional
   - Ideal para plano BÁSICO

3. **RSSI Linux Provider**
   - Funciona em Linux/Raspberry Pi com placa Wi-Fi
   - Usa comandos `iwconfig` ou `iw`
   - Requer: `sudo apt-get install wireless-tools iw`
   - Ideal para plano BÁSICO

4. **Mock Provider** (fallback)
   - Simulação para desenvolvimento/testes
   - Não captura sinais reais

## 🚀 Como Usar

### Uso Automático (Recomendado)

O sistema detecta automaticamente. Não precisa fazer nada!

```python
from app.capture.provider_factory import create_auto_provider

# Detecta e cria o melhor provider disponível
provider = create_auto_provider()
await provider.start()
signal = await provider.get_signal()
```

### Forçar Provider Específico

```python
from app.capture.provider_factory import ProviderFactory

# Forçar RSSI Windows
provider = ProviderFactory.create_provider(force_provider='rssi_windows')

# Forçar Mock para testes
provider = ProviderFactory.create_provider(force_mock=True)
```

## 🔍 Diagnóstico

Execute o script de diagnóstico para verificar seu sistema:

```bash
cd backend
python diagnostico_provider.py
```

Saída esperada:
```
📊 INFORMAÇÕES DO SISTEMA
  system: Windows
  detected_provider: RSSI Windows
  
🔍 PROVIDERS DISPONÍVEIS
  csi                  ✗ Não disponível
  rssi_windows         ✓ Disponível
  rssi_linux           ✗ Não disponível
  mock                 ✓ Disponível

🎯 PROVIDER SELECIONADO
  Tipo: RssiWindowsProvider
  Disponível: True

🧪 TESTE DE CAPTURA
  ✓ Sinal capturado:
    - RSSI: -45.0 dBm
    - Provider: rssi_windows
```

## 💼 Modelo SaaS - Planos

### Plano BÁSICO (RSSI)
- Funciona em qualquer computador com Wi-Fi
- Windows: funciona imediatamente
- Linux/Raspberry: requer `wireless-tools` e `iw`
- Detecção de presença e movimento
- Precisão: boa

### Plano PREMIUM (CSI)
- Requer hardware específico (Raspberry Pi + placa CSI)
- Detecção de presença, movimento e quedas
- Análise avançada de padrões
- Precisão: excelente

## 🛠️ Instalação por Sistema

### Windows
✅ Nenhuma instalação necessária!
- O sistema usa `netsh` que já vem no Windows
- Funciona com qualquer placa Wi-Fi

### Linux/Raspberry Pi
```bash
# Instalar ferramentas Wi-Fi
sudo apt-get update
sudo apt-get install wireless-tools iw

# Verificar instalação
iwconfig
iw dev
```

### Hardware CSI (Futuro)
Quando você comprar placas com suporte a CSI:

1. **Intel 5300**
   - Instalar driver modificado
   - Compilar ferramenta de extração CSI
   - Implementar `CsiProvider` real

2. **ESP32-S3**
   - Flashear firmware com CSI
   - Conectar via serial/WiFi
   - Implementar `CsiProvider` real

3. **Atheros CSI Tool**
   - Instalar driver modificado
   - Configurar modo monitor
   - Implementar `CsiProvider` real

## 📊 API de Diagnóstico

### Verificar Providers Disponíveis

```python
from app.capture.provider_factory import ProviderFactory

# Retorna dict com disponibilidade
available = ProviderFactory.get_available_providers()
# {'csi': False, 'rssi_windows': True, 'rssi_linux': False, 'mock': True}
```

### Obter Informações do Sistema

```python
info = ProviderFactory.get_provider_info()
# {
#   'system': 'Windows',
#   'python_version': '3.11.0',
#   'detected_provider': 'RSSI Windows',
#   'available_providers': "{'csi': False, 'rssi_windows': True, ...}",
#   'recommendation': 'Sistema Windows OK - usando RSSI nativo'
# }
```

## 🔄 Integração com Monitor Service

O `MonitorService` agora usa auto-detecção automaticamente:

```python
# backend/app/services/monitor_service.py
from app.capture.provider_factory import create_auto_provider

def __init__(self):
    # Auto-detecção ativada!
    self._provider = create_auto_provider()
```

## 🎯 Para o Modelo SaaS

### No Painel Administrativo (Futuro)

Você poderá ver para cada cliente:
- Qual provider está usando (CSI ou RSSI)
- Sistema operacional
- Status da conexão
- Plano contratado vs hardware detectado

### Validação de Plano

```python
# Exemplo de validação futura
def validate_plan(customer_plan: str, detected_provider: str):
    if customer_plan == 'premium' and detected_provider != 'csi':
        # Cliente pagou por CSI mas não tem hardware
        return False, "Hardware CSI não detectado"
    return True, "OK"
```

## 🐛 Troubleshooting

### Linux: "iwconfig: command not found"
```bash
sudo apt-get install wireless-tools iw
```

### Windows: "Nenhuma rede detectada"
- Verifique se o Wi-Fi está ligado
- Conecte-se a uma rede Wi-Fi
- Execute como Administrador

### Mock Provider sendo usado
- Verifique se tem placa Wi-Fi instalada
- No Linux, instale `wireless-tools` e `iw`
- Execute o diagnóstico: `python diagnostico_provider.py`

## 📝 Próximos Passos

1. ✅ Auto-detecção implementada
2. ⏳ Implementar CSI Provider real (quando comprar hardware)
3. ⏳ Adicionar validação de plano no backend
4. ⏳ Criar painel administrativo com info de hardware
5. ⏳ Sistema de licenciamento por tipo de hardware

## 🔗 Arquivos Relacionados

- `backend/app/capture/provider_factory.py` - Factory de auto-detecção
- `backend/app/capture/rssi_windows.py` - Provider Windows
- `backend/app/capture/rssi_linux.py` - Provider Linux/Raspberry
- `backend/app/capture/csi_placeholder.py` - Placeholder CSI (futuro)
- `backend/diagnostico_provider.py` - Script de diagnóstico
