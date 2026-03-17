# 🔌 Guia de Integração com Hardware Real

Este documento explica como integrar o WiFiSense Local com hardware real de captura de sinais Wi-Fi (RSSI e CSI).

---

## 📡 Opção 1: Captura RSSI (Mais Simples)

RSSI (Received Signal Strength Indicator) é a medida da potência do sinal recebido. É mais fácil de capturar, mas menos preciso que CSI.

### Hardware Compatível

- **Qualquer adaptador Wi-Fi** em modo monitor
- Recomendados:
  - Alfa AWUS036ACH
  - TP-Link TL-WN722N v1
  - Panda PAU09
  - Adaptadores Atheros AR9271

### Bibliotecas Python

#### Opção A: Scapy
```bash
pip install scapy
```

```python
# backend/app/capture/rssi_provider.py
from scapy.all import sniff, Dot11
from app.capture.base import SignalData, SignalProvider
import time

class RssiProvider(SignalProvider):
    def __init__(self, interface: str = "wlan0mon"):
        self.interface = interface
        self.last_rssi = -70.0
        self._running = False
    
    async def start(self) -> None:
        self._running = True
        # Coloque interface em modo monitor
        # sudo ifconfig wlan0 down
        # sudo iwconfig wlan0 mode monitor
        # sudo ifconfig wlan0 up
    
    async def stop(self) -> None:
        self._running = False
    
    async def get_signal(self) -> SignalData:
        # Captura pacotes por 0.1s
        packets = sniff(
            iface=self.interface,
            count=10,
            timeout=0.1,
            filter="type mgt subtype beacon"
        )
        
        if packets:
            # Extrai RSSI do último pacote
            rssi_values = []
            for pkt in packets:
                if pkt.haslayer(Dot11):
                    # dBm_AntSignal está no RadioTap header
                    if hasattr(pkt, 'dBm_AntSignal'):
                        rssi_values.append(pkt.dBm_AntSignal)
            
            if rssi_values:
                self.last_rssi = sum(rssi_values) / len(rssi_values)
        
        return SignalData(
            rssi=self.last_rssi,
            csi_amplitude=[],  # RSSI não tem CSI
            timestamp=time.time(),
            provider="rssi_scapy",
            metadata={"interface": self.interface}
        )
```

#### Opção B: PyShark (Wireshark wrapper)
```bash
pip install pyshark
```

```python
import pyshark
import asyncio

class RssiProviderPyShark(SignalProvider):
    def __init__(self, interface: str = "wlan0mon"):
        self.interface = interface
        self.capture = None
        self.last_rssi = -70.0
    
    async def start(self) -> None:
        self.capture = pyshark.LiveCapture(
            interface=self.interface,
            bpf_filter='wlan type mgt subtype beacon'
        )
    
    async def stop(self) -> None:
        if self.capture:
            self.capture.close()
    
    async def get_signal(self) -> SignalData:
        try:
            # Captura 1 pacote
            packet = await asyncio.wait_for(
                asyncio.to_thread(self.capture.next),
                timeout=0.5
            )
            
            if hasattr(packet, 'radiotap'):
                rssi = int(packet.radiotap.dbm_antsignal)
                self.last_rssi = rssi
        except asyncio.TimeoutError:
            pass  # Usa último valor
        
        return SignalData(
            rssi=self.last_rssi,
            csi_amplitude=[],
            timestamp=time.time(),
            provider="rssi_pyshark",
            metadata={}
        )
```

### Configuração Linux

```bash
# 1. Instalar ferramentas
sudo apt-get install aircrack-ng wireless-tools

# 2. Identificar interface
iwconfig

# 3. Colocar em modo monitor
sudo airmon-ng start wlan0

# 4. Verificar
iwconfig  # Deve aparecer wlan0mon

# 5. Testar captura
sudo tcpdump -i wlan0mon -c 10
```

### Configuração Windows

Windows não suporta modo monitor nativamente. Opções:

1. **Usar WSL2 com USB passthrough**
2. **Usar Npcap** (limitado)
3. **Usar máquina virtual Linux**

---

## 📊 Opção 2: Captura CSI (Mais Preciso)

CSI (Channel State Information) fornece informações detalhadas sobre o canal de comunicação, incluindo amplitude e fase de cada subportadora.

### Hardware Compatível

#### A. Intel 5300 NIC (Mais Popular)
- **Modelo**: Intel WiFi Link 5300
- **Interface**: Mini PCIe
- **Subportadoras**: 30 (20 MHz) ou 56 (40 MHz)
- **Driver**: Linux CSI Tool

**Instalação**:
```bash
# 1. Clonar repositório
git clone https://github.com/dhalperi/linux-80211n-csitool.git
cd linux-80211n-csitool

# 2. Compilar driver
make -C /lib/modules/$(uname -r)/build M=$(pwd)/drivers/net/wireless/iwlwifi modules

# 3. Instalar
sudo make -C /lib/modules/$(uname -r)/build M=$(pwd)/drivers/net/wireless/iwlwifi INSTALL_MOD_DIR=updates modules_install
sudo depmod

# 4. Carregar módulo
sudo modprobe iwlwifi connector_log=0x1
```

**Captura**:
```python
# backend/app/capture/csi_intel5300.py
import struct
import socket
from app.capture.base import SignalData, SignalProvider

class Intel5300CsiProvider(SignalProvider):
    def __init__(self):
        self.sock = None
        self._running = False
    
    async def start(self) -> None:
        # Conecta ao netlink socket do driver
        self.sock = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, 16)
        self.sock.bind((0, 0))
        self._running = True
    
    async def stop(self) -> None:
        self._running = False
        if self.sock:
            self.sock.close()
    
    async def get_signal(self) -> SignalData:
        # Recebe dados CSI do driver
        data = await asyncio.to_thread(self.sock.recv, 4096)
        
        # Parse do formato Intel 5300
        # Estrutura: timestamp, csi_len, tx_channel, err_info, noise_floor, Rate, bandWidth, num_tones, nr, nc, rssi, rssi_1, rssi_2, rssi_3, payload_len, CSI data
        
        # Simplificado - veja documentação completa do CSI Tool
        csi_data = self._parse_csi(data)
        
        return SignalData(
            rssi=csi_data['rssi'],
            csi_amplitude=csi_data['amplitudes'],
            timestamp=time.time(),
            provider="intel5300",
            metadata=csi_data['metadata']
        )
    
    def _parse_csi(self, data: bytes) -> dict:
        # Parse específico do formato Intel 5300
        # Retorna amplitudes das 30 subportadoras
        # Veja: https://dhalperi.github.io/linux-80211n-csitool/
        
        # Exemplo simplificado
        num_subcarriers = 30
        amplitudes = []
        
        # CSI data começa após header
        offset = 25  # Tamanho do header
        for i in range(num_subcarriers):
            # Cada subportadora: real (2 bytes) + imaginário (2 bytes)
            real = struct.unpack('h', data[offset:offset+2])[0]
            imag = struct.unpack('h', data[offset+2:offset+4])[0]
            amplitude = (real**2 + imag**2) ** 0.5
            amplitudes.append(amplitude)
            offset += 4
        
        return {
            'rssi': -50.0,  # Extrair do header
            'amplitudes': amplitudes,
            'metadata': {'num_subcarriers': num_subcarriers}
        }
```

#### B. ESP32-S3 (Mais Acessível)
- **Modelo**: ESP32-S3 com Wi-Fi 802.11n
- **Subportadoras**: 64 (HT20) ou 128 (HT40)
- **SDK**: ESP-IDF com CSI

**Firmware ESP32**:
```c
// main.c
#include "esp_wifi.h"
#include "esp_wifi_types.h"

void wifi_csi_rx_cb(void *ctx, wifi_csi_info_t *data) {
    // Envia CSI via Serial ou TCP
    int8_t *csi_data = data->buf;
    int len = data->len;
    
    // Enviar para Python via Serial
    printf("CSI:%d:", len);
    for (int i = 0; i < len; i++) {
        printf("%d,", csi_data[i]);
    }
    printf("\n");
}

void app_main() {
    // Configurar Wi-Fi
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    
    // Habilitar CSI
    wifi_csi_config_t csi_config = {
        .lltf_en = true,
        .htltf_en = true,
        .stbc_htltf2_en = true,
        .ltf_merge_en = true,
        .channel_filter_en = false,
        .manu_scale = false
    };
    esp_wifi_set_csi_config(&csi_config);
    esp_wifi_set_csi_rx_cb(&wifi_csi_rx_cb, NULL);
    esp_wifi_set_csi(true);
}
```

**Python (Backend)**:
```python
# backend/app/capture/csi_esp32.py
import serial
import asyncio

class ESP32CsiProvider(SignalProvider):
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200):
        self.serial = serial.Serial(port, baudrate, timeout=1)
        self._running = False
    
    async def start(self) -> None:
        self._running = True
    
    async def stop(self) -> None:
        self._running = False
        self.serial.close()
    
    async def get_signal(self) -> SignalData:
        # Lê linha da serial
        line = await asyncio.to_thread(self.serial.readline)
        line = line.decode('utf-8').strip()
        
        if line.startswith("CSI:"):
            # Parse: "CSI:128:val1,val2,val3,..."
            parts = line.split(':')
            length = int(parts[1])
            values = [int(x) for x in parts[2].split(',') if x]
            
            # Converte para amplitudes
            amplitudes = []
            for i in range(0, len(values), 2):
                if i+1 < len(values):
                    real = values[i]
                    imag = values[i+1]
                    amp = (real**2 + imag**2) ** 0.5
                    amplitudes.append(amp)
            
            return SignalData(
                rssi=-50.0,  # ESP32 também fornece RSSI
                csi_amplitude=amplitudes,
                timestamp=time.time(),
                provider="esp32_csi",
                metadata={"num_subcarriers": len(amplitudes)}
            )
        
        # Fallback
        return SignalData(
            rssi=-70.0,
            csi_amplitude=[],
            timestamp=time.time(),
            provider="esp32_csi",
            metadata={}
        )
```

#### C. Atheros AR9271 (Alternativa)
- **Modelo**: Atheros AR9271 (TP-Link TL-WN722N v1)
- **Driver**: Atheros CSI Tool
- **Repositório**: https://github.com/xieyaxiongfly/Atheros-CSI-Tool

---

## 🔄 Integração no Sistema

### 1. Adicionar Provider ao Projeto

```python
# backend/app/capture/__init__.py
from .mock_provider import MockSignalProvider
from .rssi_provider import RssiProvider  # Novo
from .csi_intel5300 import Intel5300CsiProvider  # Novo
from .csi_esp32 import ESP32CsiProvider  # Novo

__all__ = [
    'MockSignalProvider',
    'RssiProvider',
    'Intel5300CsiProvider',
    'ESP32CsiProvider',
]
```

### 2. Registrar no ConfigService

```python
# backend/app/services/config_service.py
AVAILABLE_PROVIDERS = {
    'mock': MockSignalProvider,
    'rssi': RssiProvider,
    'intel5300': Intel5300CsiProvider,
    'esp32': ESP32CsiProvider,
}

def get_provider(name: str) -> SignalProvider:
    provider_class = AVAILABLE_PROVIDERS.get(name)
    if not provider_class:
        raise ValueError(f"Provider '{name}' não encontrado")
    return provider_class()
```

### 3. Atualizar MonitorService

```python
# backend/app/services/monitor_service.py
def set_provider(self, provider_name: str) -> None:
    """Troca o provider ativo."""
    if self._is_running:
        raise RuntimeError("Pare o monitoramento antes de trocar provider")
    
    self._provider = config_service.get_provider(provider_name)
```

### 4. Adicionar Rota na API

```python
# backend/app/api/routes.py
@router.post("/provider/set")
async def set_provider(provider: str):
    """Troca o provider ativo."""
    try:
        monitor_service.set_provider(provider)
        return {"status": "ok", "provider": provider}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/providers")
async def list_providers():
    """Lista providers disponíveis."""
    from app.services.config_service import AVAILABLE_PROVIDERS
    return {
        "providers": [
            {
                "name": name,
                "available": cls().is_available() if hasattr(cls(), 'is_available') else True
            }
            for name, cls in AVAILABLE_PROVIDERS.items()
        ]
    }
```

### 5. Atualizar Frontend

```typescript
// frontend/src/services/api.ts
export const api = {
  // ... métodos existentes
  
  listProviders: () => 
    request<{ providers: Array<{ name: string; available: boolean }> }>('/providers'),
  
  setProvider: (provider: string) =>
    request<{ status: string; provider: string }>('/provider/set', {
      method: 'POST',
      body: JSON.stringify({ provider }),
    }),
}
```

```tsx
// frontend/src/pages/Settings.tsx
// Adicionar seletor dinâmico de providers
const [providers, setProviders] = useState([]);

useEffect(() => {
  api.listProviders().then(data => setProviders(data.providers));
}, []);

// No render:
<select value={config.active_provider} onChange={handleProviderChange}>
  {providers.map(p => (
    <option key={p.name} value={p.name} disabled={!p.available}>
      {p.name} {!p.available && '(indisponível)'}
    </option>
  ))}
</select>
```

---

## 🧪 Testando a Integração

### 1. Teste Básico
```python
# test_provider.py
import asyncio
from app.capture.rssi_provider import RssiProvider

async def test():
    provider = RssiProvider(interface="wlan0mon")
    await provider.start()
    
    for i in range(10):
        signal = await provider.get_signal()
        print(f"RSSI: {signal.rssi} dBm")
        await asyncio.sleep(0.5)
    
    await provider.stop()

asyncio.run(test())
```

### 2. Validação de Dados
```python
# Verificar se os dados fazem sentido
assert -100 <= signal.rssi <= -20, "RSSI fora do range esperado"
assert len(signal.csi_amplitude) > 0, "CSI vazio"
assert all(amp >= 0 for amp in signal.csi_amplitude), "Amplitudes negativas"
```

### 3. Comparação com Mock
```python
# Compare features extraídas do mock vs real
mock_features = processor.process(mock_signal)
real_features = processor.process(real_signal)

print(f"Mock energy: {mock_features.signal_energy}")
print(f"Real energy: {real_features.signal_energy}")
```

---

## 📈 Calibração

Após integrar hardware real, você precisará calibrar os limiares:

### 1. Coletar Dados de Referência
```python
# collect_calibration_data.py
import asyncio
import json

async def collect(scenario: str, duration: int = 60):
    provider = RssiProvider()
    processor = SignalProcessor()
    await provider.start()
    
    samples = []
    for _ in range(duration * 2):  # 2 Hz
        signal = await provider.get_signal()
        features = processor.process(signal)
        samples.append({
            'scenario': scenario,
            'rssi': signal.rssi,
            'energy': features.signal_energy,
            'variance': features.signal_variance,
            'rate': features.rate_of_change,
        })
        await asyncio.sleep(0.5)
    
    await provider.stop()
    
    with open(f'calibration_{scenario}.json', 'w') as f:
        json.dump(samples, f)

# Coletar para cada cenário
asyncio.run(collect('empty', 60))
asyncio.run(collect('still', 60))
asyncio.run(collect('moving', 60))
```

### 2. Analisar Estatísticas
```python
import json
import numpy as np

def analyze(scenario: str):
    with open(f'calibration_{scenario}.json') as f:
        data = json.load(f)
    
    energies = [s['energy'] for s in data]
    variances = [s['variance'] for s in data]
    
    print(f"\n{scenario.upper()}:")
    print(f"  Energy: mean={np.mean(energies):.2f}, std={np.std(energies):.2f}")
    print(f"  Variance: mean={np.mean(variances):.2f}, std={np.std(variances):.2f}")

analyze('empty')
analyze('still')
analyze('moving')
```

### 3. Ajustar Limiares
```python
# backend/app/detection/heuristic_detector.py
# Atualizar ThresholdConfig com valores calibrados

@dataclass
class ThresholdConfig:
    presence_energy_min: float = 6.5  # Ajustado após calibração
    movement_variance_min: float = 3.2  # Ajustado após calibração
    fall_rate_spike: float = 15.0  # Ajustado após calibração
    # ...
```

---

## 🚨 Troubleshooting

### Problema: RSSI sempre -70 dBm
- Verifique se interface está em modo monitor
- Teste com `tcpdump -i wlan0mon`
- Verifique permissões (precisa de root/sudo)

### Problema: CSI vazio
- Verifique se driver CSI está carregado: `lsmod | grep iwlwifi`
- Verifique logs do kernel: `dmesg | grep iwlwifi`
- Teste ferramenta de exemplo do CSI Tool

### Problema: Muitos pacotes perdidos
- Reduza `sampling_interval` nas configurações
- Use buffer maior no provider
- Verifique carga da CPU

### Problema: Detecção imprecisa
- Calibre limiares com dados reais
- Aumente janela temporal do processor
- Considere treinar modelo ML

---

## 📚 Recursos Adicionais

### Documentação
- Intel 5300 CSI Tool: https://dhalperi.github.io/linux-80211n-csitool/
- Atheros CSI Tool: https://github.com/xieyaxiongfly/Atheros-CSI-Tool
- ESP32 CSI: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html#wi-fi-channel-state-information

### Papers
- "FIFS: Fine-grained Indoor Fingerprinting System" (MobiCom 2012)
- "E-eyes: Device-free Location-oriented Activity Identification" (MobiCom 2014)
- "WiFall: Device-free Fall Detection by Wireless Networks" (INFOCOM 2014)

### Datasets Públicos
- CSI Dataset for Human Activity Recognition: http://tns.thss.tsinghua.edu.cn/wifiradar/
- UT-HAR Dataset: https://github.com/ermongroup/Wifi_Activity_Recognition

---

**Com hardware real, o WiFiSense Local se torna um sistema de monitoramento profissional!**
