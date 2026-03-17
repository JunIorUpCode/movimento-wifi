# 🎯 Sonar Wi-Fi: Visualização de Formas Reais

## 🎨 O QUE VOCÊ VIU NO DASHBOARD

Implementei uma **simulação visual** tipo sonar que mostra o conceito, mas...

⚠️ **IMPORTANTE**: Com RSSI atual, NÃO é possível ver formas reais de pessoas/objetos.

---

## 🔬 POR QUE NÃO FUNCIONA COM RSSI?

### Analogia Simples

**RSSI é como:**
- Ter 1 microfone em uma sala escura
- Você ouve "tem barulho" ou "não tem barulho"
- Mas não sabe ONDE está ou QUAL é a forma

**CSI é como:**
- Ter 30-128 microfones em frequências diferentes
- Cada um "ouve" o ambiente de forma única
- Juntos, podem "ver" formas e posições

---

## 📊 COMPARAÇÃO TÉCNICA

| Aspecto | RSSI (Atual) | CSI (Necessário) |
|---------|--------------|------------------|
| **Dados** | 1 número (-62 dBm) | 30-128 valores complexos |
| **Informação** | Potência total | Amplitude + Fase por subportadora |
| **Resolução** | Baixa | Alta |
| **Espacial** | ❌ Não | ✅ Sim |
| **Formas** | ❌ Não | ✅ Sim (com processamento) |
| **Hardware** | Qualquer Wi-Fi | Intel 5300, ESP32-S3, etc |

---

## 🎯 O QUE É POSSÍVEL FAZER

### Com RSSI (O Que Temos)

✅ **Possível:**
- Detectar presença/ausência
- Detectar movimento geral
- Estimar distância aproximada (perto/longe)
- Contar número aproximado de pessoas (impreciso)

❌ **Impossível:**
- Ver formas de pessoas
- Distinguir pessoa de cachorro
- Saber posição exata
- Tracking preciso
- Reconhecer gestos específicos

### Com CSI (Hardware Especial)

✅ **Possível:**
- Ver "silhuetas" de pessoas
- Distinguir múltiplas pessoas
- Tracking de posição
- Reconhecer gestos
- Detectar respiração
- Identificar atividades

---

## 🛠️ COMO FAZER DE VERDADE

### Opção 1: Hardware CSI Básico (ESP32-S3)

**Custo:** ~R$ 50-100
**Dificuldade:** Média
**Precisão:** Boa

#### Passo 1: Comprar Hardware
```
ESP32-S3-DevKitC-1
- Wi-Fi 802.11n
- Suporte a CSI
- USB para programação
```

#### Passo 2: Firmware
```c
// Código ESP32 para capturar CSI
#include "esp_wifi.h"

void wifi_csi_rx_cb(void *ctx, wifi_csi_info_t *data) {
    // Captura CSI de 64 ou 128 subportadoras
    int8_t *csi_data = data->buf;
    int len = data->len;
    
    // Envia via Serial ou TCP
    for (int i = 0; i < len; i += 2) {
        int8_t real = csi_data[i];
        int8_t imag = csi_data[i+1];
        float amplitude = sqrt(real*real + imag*imag);
        float phase = atan2(imag, real);
        
        // Processa amplitude e fase
    }
}
```

#### Passo 3: Processamento
```python
# backend/app/processing/csi_imaging.py
import numpy as np

def reconstruct_image(csi_data):
    """
    Reconstrói imagem 2D do ambiente usando CSI
    """
    # 1. Extrai amplitude e fase
    amplitudes = np.abs(csi_data)
    phases = np.angle(csi_data)
    
    # 2. Aplica MUSIC ou SAGE algorithm
    # (Multiple Signal Classification)
    angles = music_algorithm(csi_data)
    
    # 3. Cria imagem 2D
    image = np.zeros((100, 100))
    for angle, distance in zip(angles, distances):
        x = int(50 + distance * np.cos(angle))
        y = int(50 + distance * np.sin(angle))
        if 0 <= x < 100 and 0 <= y < 100:
            image[y, x] = 1
    
    return image
```

---

### Opção 2: Hardware CSI Profissional (Intel 5300)

**Custo:** ~R$ 200-500 (usado)
**Dificuldade:** Alta
**Precisão:** Excelente

#### Hardware Necessário
```
- Intel WiFi Link 5300 (placa Mini PCIe)
- Computador com slot Mini PCIe
- Linux (Ubuntu recomendado)
- 3 antenas externas
```

#### Software
```bash
# Linux CSI Tool
git clone https://github.com/dhalperi/linux-80211n-csitool.git
cd linux-80211n-csitool
make
sudo make install
```

#### Captura
```python
# Captura CSI com 30 subportadoras
# Cada subportadora tem amplitude e fase
# Total: 30 valores complexos por pacote
```

---

### Opção 3: Sistema Completo (Múltiplos APs)

**Custo:** ~R$ 1000-3000
**Dificuldade:** Muito Alta
**Precisão:** Profissional

#### Setup
```
3-4 Pontos de Acesso com CSI
    ↓
Triangulação
    ↓
Reconstrução 3D
    ↓
Machine Learning
    ↓
Formas Reais!
```

---

## 🧠 ALGORITMOS NECESSÁRIOS

### 1. MUSIC (Multiple Signal Classification)
```python
def music_algorithm(csi_matrix):
    """
    Estima ângulos de chegada dos sinais
    """
    # 1. Calcula matriz de covariância
    R = np.dot(csi_matrix, csi_matrix.conj().T)
    
    # 2. Decomposição em autovalores
    eigenvalues, eigenvectors = np.linalg.eig(R)
    
    # 3. Separa sinal de ruído
    signal_space = eigenvectors[:, :num_signals]
    noise_space = eigenvectors[:, num_signals:]
    
    # 4. Calcula espectro MUSIC
    angles = []
    for theta in np.linspace(0, 180, 180):
        steering_vector = compute_steering_vector(theta)
        spectrum = 1 / np.abs(np.dot(steering_vector.conj().T, 
                                     np.dot(noise_space, noise_space.conj().T), 
                                     steering_vector))
        angles.append((theta, spectrum))
    
    return angles
```

### 2. Beamforming
```python
def beamforming(csi_data, angle):
    """
    Foca o "feixe" em uma direção específica
    """
    steering_vector = np.exp(-1j * 2 * np.pi * d * np.sin(angle) / wavelength)
    output = np.dot(steering_vector.conj(), csi_data)
    return output
```

### 3. Reconstrução de Imagem
```python
def reconstruct_2d_image(csi_data, num_angles=360):
    """
    Cria imagem 2D do ambiente
    """
    image = np.zeros((200, 200))
    
    for angle in range(num_angles):
        # Beamforming em cada ângulo
        power = beamforming(csi_data, angle * np.pi / 180)
        
        # Estima distância
        distance = estimate_distance(power)
        
        # Plota no mapa
        x = int(100 + distance * np.cos(angle * np.pi / 180))
        y = int(100 + distance * np.sin(angle * np.pi / 180))
        
        if 0 <= x < 200 and 0 <= y < 200:
            image[y, x] = np.abs(power)
    
    return image
```

---

## 📚 PAPERS DE REFERÊNCIA

### Detecção de Formas com Wi-Fi

1. **"Through-Wall Human Pose Estimation Using Radio Signals"** (CVPR 2018)
   - MIT
   - Detecta pose humana através de paredes
   - Usa CSI de múltiplos APs

2. **"RF-Pose: 3D Human Pose Estimation using WiFi"** (CVPR 2019)
   - MIT
   - Reconstrução 3D de poses
   - Deep Learning + CSI

3. **"Person-in-WiFi: Fine-grained Person Perception using WiFi"** (ICCV 2019)
   - UC Santa Barbara
   - Segmentação de pessoas
   - Tracking multi-pessoa

4. **"Widar3.0: Zero-Effort Cross-Domain Gesture Recognition"** (MobiCom 2020)
   - Reconhecimento de gestos
   - Transfer learning

---

## 💰 CUSTO vs BENEFÍCIO

| Solução | Custo | Precisão | Formas Reais? |
|---------|-------|----------|---------------|
| **RSSI (atual)** | R$ 0 | Baixa | ❌ Não |
| **ESP32-S3** | R$ 50-100 | Média | ⚠️ Parcial |
| **Intel 5300** | R$ 200-500 | Alta | ✅ Sim |
| **Sistema Completo** | R$ 1000-3000 | Profissional | ✅ Sim (HD) |

---

## 🎯 RECOMENDAÇÃO

### Para Você Agora

1. **Continue com RSSI** para:
   - Detecção de presença
   - Monitoramento de movimento
   - Alertas de queda
   - Protótipo funcional

2. **Upgrade para ESP32-S3** se quiser:
   - Melhor precisão
   - Custo baixo (~R$ 50)
   - Aprender CSI
   - Projeto DIY

3. **Sistema Profissional** apenas se:
   - Projeto comercial
   - Pesquisa acadêmica
   - Orçamento disponível
   - Equipe técnica

---

## 🔮 FUTURO DO PROJETO

### Roadmap para Formas Reais

**Fase 1: RSSI (✅ CONCLUÍDO)**
- Detecção básica
- Dashboard funcional
- Alertas

**Fase 2: CSI Básico (📅 Futuro)**
- Comprar ESP32-S3
- Implementar captura CSI
- Melhorar precisão

**Fase 3: Imaging (📅 Futuro)**
- Algoritmos MUSIC/SAGE
- Reconstrução 2D
- Visualização de formas

**Fase 4: Machine Learning (📅 Futuro)**
- Treinar modelo
- Reconhecimento de padrões
- Formas detalhadas

---

## 🎨 O QUE VOCÊ TEM AGORA

### Simulação Visual (Dashboard)
- ✅ Sonar animado
- ✅ Varredura 360°
- ✅ Objetos detectados (simulados)
- ✅ Grid radial
- ✅ Informações em tempo real

### Limitações
- ❌ Posições são estimadas (não reais)
- ❌ Formas são genéricas (não específicas)
- ❌ Baseado em RSSI (1 valor)
- ❌ Sem informação espacial real

### Mas É Útil Para
- ✅ Visualizar conceito
- ✅ Entender como funcionaria
- ✅ Demonstração
- ✅ Protótipo

---

## 📞 CONCLUSÃO

**Resposta Direta:**
- Com RSSI: ❌ Não dá para ver formas reais
- Com CSI: ✅ Sim, é possível!
- Custo mínimo: ~R$ 50 (ESP32-S3)
- Complexidade: Alta (requer estudo)

**O Que Fiz:**
- ✅ Criei simulação visual (conceito)
- ✅ Mostra como seria
- ✅ Funciona com dados atuais
- ✅ Base para futuro upgrade

**Próximo Passo:**
- Decidir se quer investir em CSI
- Estudar algoritmos (MUSIC, beamforming)
- Comprar hardware (ESP32-S3)
- Implementar captura real

---

**A tecnologia existe, mas requer hardware especial e algoritmos complexos!**

Veja papers do MIT e UC Santa Barbara para exemplos reais de sistemas que fazem isso.
