# 🏠 Guia de Instalação - Como Funciona na Prática

## 🎯 Cenário Real: Casa do Seu Sogro

Vamos usar o exemplo que você deu para explicar TUDO.

---

## 📦 Plano Básico (RSSI) - Como Instalar

### O Que o Cliente Precisa Ter:
- ✅ Roteador Wi-Fi (qualquer um que ele já tem)
- ✅ Computador ligado 24/7 (pode ser um PC velho, Raspberry Pi, etc.)
- ✅ Internet funcionando

### Passo a Passo da Instalação:

#### 1. Você Vende o Serviço
```
Cliente: "Quero monitorar minha casa enquanto viajo"
Você: "Perfeito! Temos o Plano Básico por R$ 99/mês"
```

#### 2. Você Agenda a Instalação
```
Opção A: Você vai na casa dele instalar
Opção B: Você envia um técnico
Opção C: Instalação remota (TeamViewer/AnyDesk)
```

#### 3. Instalação Física (5-10 minutos)
```
1. Ligar um computador na casa dele
   - Pode ser: PC velho, Raspberry Pi ($35), Mini PC ($100)
   - Deixar ligado 24/7 conectado no Wi-Fi

2. Instalar seu software nesse computador
   - Windows: Executar instalador.exe
   - Linux: Executar script de instalação
   - Raspberry Pi: Gravar cartão SD com imagem pronta

3. Configurar Telegram dele
   - Criar bot do Telegram
   - Adicionar número dele
   - Testar alertas

4. Pronto! Sistema funcionando
```

#### 4. Como Funciona Depois
```
Casa vazia → Detecta movimento → Alerta no Telegram dele
```

**Custo para o cliente:**
- Hardware: R$ 150-500 (computador/Raspberry Pi) - COMPRA ÚNICA
- Mensalidade: R$ 99/mês (seu serviço)

---

## 🚀 Plano Premium (CSI) - Como Fazer Upgrade

### Quando o Cliente Quer Upgrade:

```
Cliente: "Quero ver no mapa ONDE a pessoa está"
Você: "Perfeito! Fazemos upgrade para Plano Premium por R$ 299/mês"
```

### O Que Muda na Instalação:

#### 1. Você Compra o Hardware CSI
```
Opções:
A) ESP32-CSI: $10 (R$ 50)
B) Intel 5300: $80 (R$ 400)
C) Raspberry Pi + Nexmon: $50 (R$ 250)
```

#### 2. Você Instala o Hardware CSI
```
Cenário A - ESP32 (Mais Simples):
1. Comprar ESP32 na AliExpress/Amazon
2. Conectar ESP32 via USB no computador
3. Instalar driver/firmware no ESP32
4. Seu software detecta automaticamente
5. Ativa visualização em mapa

Cenário B - Intel 5300 (Mais Profissional):
1. Comprar placa Intel 5300
2. Abrir o computador
3. Instalar placa no slot PCI
4. Instalar driver Linux
5. Seu software detecta automaticamente
6. Ativa visualização em mapa

Cenário C - Raspberry Pi (Mais Fácil):
1. Comprar Raspberry Pi 4
2. Instalar firmware Nexmon CSI
3. Conectar na rede
4. Seu software detecta automaticamente
5. Ativa visualização em mapa
```

#### 3. Seu Software Detecta Automaticamente
```python
# Seu código detecta qual hardware está disponível
if csi_hardware_detected():
    modo = "CSI - Visualização Premium"
    mostrar_mapa = True
else:
    modo = "RSSI - Detecção Básica"
    mostrar_mapa = False
```

---

## 💼 Modelos de Negócio

### Modelo 1: Você Fornece o Hardware (Recomendado)

**Plano Básico - R$ 99/mês**
```
Inclui:
- Hardware (Raspberry Pi) em comodato
- Software WiFiSense
- Alertas no Telegram
- Detecção de movimento/queda
- Suporte técnico

Cliente paga: R$ 99/mês
Seu custo: R$ 150 (hardware) + R$ 10/mês (servidor)
Lucro: R$ 89/mês após 2 meses
```

**Plano Premium - R$ 299/mês**
```
Inclui:
- Tudo do Básico +
- Hardware CSI (ESP32 ou Intel 5300)
- Visualização em mapa
- Localização exata
- Rastreamento múltiplas pessoas
- Suporte prioritário

Cliente paga: R$ 299/mês
Seu custo: R$ 200 (hardware) + R$ 10/mês (servidor)
Lucro: R$ 289/mês após 1 mês
```

### Modelo 2: Cliente Compra o Hardware

**Plano Básico - R$ 49/mês**
```
Cliente compra:
- Raspberry Pi 4 (R$ 250)

Cliente paga mensalmente:
- R$ 49/mês (software + suporte)

Seu lucro: R$ 39/mês (sem custo de hardware)
```

**Plano Premium - R$ 149/mês**
```
Cliente compra:
- Raspberry Pi 4 (R$ 250)
- ESP32-CSI (R$ 50)
Total: R$ 300

Cliente paga mensalmente:
- R$ 149/mês (software + suporte)

Seu lucro: R$ 139/mês (sem custo de hardware)
```

---

## 🔧 Instalação Técnica Detalhada

### Opção 1: Raspberry Pi (Recomendado para Você)

**Por quê Raspberry Pi?**
- ✅ Pequeno (tamanho de um cartão de crédito)
- ✅ Consome pouca energia (5W)
- ✅ Silencioso (sem ventilador)
- ✅ Fácil de instalar
- ✅ Funciona com RSSI E CSI

**Instalação Básica (RSSI):**
```
1. Comprar Raspberry Pi 4 (4GB RAM) - R$ 250
2. Comprar cartão microSD 32GB - R$ 30
3. Gravar sua imagem no cartão SD
4. Conectar Raspberry Pi:
   - Cabo de energia
   - Cabo ethernet (ou Wi-Fi)
5. Ligar
6. Acessar via navegador: http://192.168.1.X:8000
7. Configurar Telegram
8. Pronto!
```

**Upgrade para Premium (CSI):**
```
1. Comprar ESP32 - R$ 50
2. Conectar ESP32 no USB do Raspberry Pi
3. Sistema detecta automaticamente
4. Ativa visualização em mapa
5. Pronto!
```

### Opção 2: Mini PC (Para Clientes Exigentes)

**Instalação:**
```
1. Comprar Mini PC (tipo Intel NUC) - R$ 800-1500
2. Instalar Windows ou Linux
3. Instalar seu software
4. Configurar para iniciar automaticamente
5. Pronto!
```

**Upgrade CSI:**
```
1. Comprar placa Intel 5300 - R$ 400
2. Abrir Mini PC
3. Instalar placa no slot M.2 ou mini-PCIe
4. Instalar driver
5. Sistema detecta automaticamente
6. Pronto!
```

---

## 📱 Interface do Cliente

### Dashboard Web (Ambos os Planos)
```
http://casa-do-sogro.wifisense.com.br

Mostra:
- Status: Monitorando / Parado
- Último evento: Movimento às 14:30
- Histórico de eventos
- Configurações de alertas
```

### Plano Básico (RSSI)
```
┌─────────────────────────────┐
│  WiFiSense - Plano Básico   │
├─────────────────────────────┤
│ Status: 🟢 Monitorando      │
│                             │
│ Último Evento:              │
│ 🚶 Movimento - 14:30        │
│ Confiança: 75%              │
│                             │
│ Histórico:                  │
│ • 14:30 - Movimento         │
│ • 14:15 - Presença          │
│ • 14:00 - Movimento         │
│                             │
│ [Configurações] [Histórico] │
└─────────────────────────────┘
```

### Plano Premium (CSI)
```
┌─────────────────────────────┐
│  WiFiSense - Plano Premium  │
├─────────────────────────────┤
│ Status: 🟢 Monitorando      │
│                             │
│ Mapa do Ambiente:           │
│ ┌───────────────────────┐   │
│ │  🟦🟦🟦🟦🟦🟦🟦🟦  │   │
│ │  🟦🟦🟩🟩🟩🟦🟦🟦  │   │
│ │  🟦🟩🟨🟨🟨🟩🟦🟦  │   │
│ │  🟦🟩🟨🔴🟨🟩🟦🟦  │ ← Pessoa
│ │  🟦🟩🟨🟨🟨🟩🟦🟦  │   │
│ │  🟦🟦🟩🟩🟩🟦🟦🟦  │   │
│ │  🟦🟦🟦🟦🟦🟦🟦🟦  │   │
│ └───────────────────────┘   │
│                             │
│ Posição: (3.5m, 2.8m)       │
│ Sala de Estar               │
│                             │
│ [Configurações] [Histórico] │
└─────────────────────────────┘
```

---

## 🎯 Processo de Venda Completo

### Passo 1: Cliente Entra em Contato
```
Cliente: "Quero monitorar minha casa"
```

### Passo 2: Você Apresenta os Planos
```
Você: "Temos 2 planos:

BÁSICO - R$ 99/mês
- Detecta movimento e quedas
- Alertas no Telegram
- Histórico de eventos
- Instalação incluída

PREMIUM - R$ 299/mês
- Tudo do Básico +
- Visualização em mapa
- Localização exata
- Rastreamento múltiplas pessoas

Qual faz mais sentido para você?"
```

### Passo 3: Cliente Escolhe
```
Cliente: "Vou começar com o Básico"
```

### Passo 4: Você Agenda Instalação
```
Você: "Perfeito! Vou agendar instalação para sexta-feira.
      Preciso de:
      - Acesso ao Wi-Fi
      - Tomada disponível
      - 30 minutos do seu tempo"
```

### Passo 5: Instalação
```
1. Você leva Raspberry Pi configurado
2. Conecta na tomada e Wi-Fi
3. Configura Telegram dele
4. Testa movimento
5. Mostra como usar
6. Pronto!
```

### Passo 6: Cliente Usa
```
Cliente viaja → Casa vazia → Detecta movimento → Alerta no Telegram
```

### Passo 7: Upgrade (Futuro)
```
Cliente: "Quero ver no mapa onde a pessoa está"
Você: "Fazemos upgrade para Premium! Vou agendar instalação do hardware CSI"

Instalação do upgrade:
1. Você leva ESP32
2. Conecta no Raspberry Pi
3. Sistema detecta automaticamente
4. Ativa visualização em mapa
5. Pronto! (15 minutos)
```

---

## 💰 Análise Financeira

### Investimento Inicial (Você)

**Para 10 Clientes Básicos:**
```
10x Raspberry Pi 4: R$ 2.500
10x Cartão SD: R$ 300
10x Fonte: R$ 200
10x Case: R$ 150
Total: R$ 3.150

Receita mensal: 10 x R$ 99 = R$ 990/mês
Payback: 3-4 meses
Lucro após 1 ano: R$ 8.730
```

**Para 10 Clientes Premium:**
```
10x Raspberry Pi 4: R$ 2.500
10x ESP32-CSI: R$ 500
10x Acessórios: R$ 650
Total: R$ 3.650

Receita mensal: 10 x R$ 299 = R$ 2.990/mês
Payback: 1-2 meses
Lucro após 1 ano: R$ 32.230
```

---

## 🔄 Fluxo de Upgrade Automático

### Como Seu Software Detecta o Hardware:

```python
# backend/app/capture/hardware_detector.py

class HardwareDetector:
    """Detecta automaticamente qual hardware está disponível."""
    
    def detect_available_hardware(self):
        """Detecta hardware e retorna capacidades."""
        
        # Tenta detectar CSI
        if self._detect_esp32_csi():
            return {
                "type": "ESP32-CSI",
                "capabilities": ["rssi", "csi", "mapping"],
                "plan": "premium"
            }
        
        elif self._detect_intel_5300():
            return {
                "type": "Intel-5300",
                "capabilities": ["rssi", "csi", "mapping", "advanced"],
                "plan": "premium"
            }
        
        elif self._detect_nexmon_csi():
            return {
                "type": "Nexmon-CSI",
                "capabilities": ["rssi", "csi", "mapping"],
                "plan": "premium"
            }
        
        # Fallback para RSSI
        else:
            return {
                "type": "RSSI-Only",
                "capabilities": ["rssi"],
                "plan": "basic"
            }
    
    def _detect_esp32_csi(self):
        """Detecta ESP32 conectado via USB."""
        # Verifica portas USB
        # Procura por dispositivo ESP32
        pass
    
    def _detect_intel_5300(self):
        """Detecta placa Intel 5300."""
        # Verifica interfaces de rede
        # Procura por Intel 5300
        pass
```

### Interface Mostra Automaticamente:

```python
# frontend/src/components/Dashboard.tsx

function Dashboard() {
    const hardware = useHardware(); // Detecta automaticamente
    
    return (
        <div>
            {hardware.plan === "premium" ? (
                <HeatmapView />  // Mostra mapa
            ) : (
                <BasicView />    // Mostra apenas eventos
            )}
        </div>
    );
}
```

---

## 📋 Checklist de Instalação

### Plano Básico (RSSI)
- [ ] Raspberry Pi configurado
- [ ] Software instalado
- [ ] Conectado no Wi-Fi do cliente
- [ ] Bot do Telegram criado
- [ ] Número do cliente adicionado
- [ ] Teste de movimento realizado
- [ ] Cliente recebeu alerta
- [ ] Treinamento do cliente concluído

### Upgrade Premium (CSI)
- [ ] Hardware CSI comprado
- [ ] Hardware CSI conectado
- [ ] Driver instalado
- [ ] Sistema detectou hardware
- [ ] Visualização em mapa ativada
- [ ] Calibração do ambiente realizada
- [ ] Teste de localização realizado
- [ ] Cliente viu mapa funcionando

---

## 🎉 Resumo Final

### Para o Cliente (Seu Sogro):

**Plano Básico:**
1. Você instala um "computadorzinho" na casa dele
2. Fica ligado 24/7 monitorando
3. Detecta movimento e envia alerta no Telegram
4. Ele não precisa fazer NADA
5. Funciona automaticamente

**Upgrade Premium:**
1. Você volta lá e instala um "chip" adicional
2. Agora ele vê no mapa ONDE a pessoa está
3. Tudo automático
4. Ele não precisa fazer NADA

### Para Você (Vendedor):

**Plano Básico:**
- Hardware: Raspberry Pi (R$ 250)
- Instalação: 30 minutos
- Mensalidade: R$ 99
- Lucro: R$ 89/mês após 3 meses

**Upgrade Premium:**
- Hardware adicional: ESP32 (R$ 50)
- Instalação: 15 minutos
- Mensalidade: R$ 299
- Lucro: R$ 289/mês após 1 mês

---

**Ficou claro agora como funciona na prática?** 🚀

O cliente não precisa saber nada de RSSI ou CSI. Você cuida de tudo!
