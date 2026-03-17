# 🍓 Guia Completo: Raspberry Pi para WiFiSense

## 🎯 O Que É Raspberry Pi?

### Definição Simples:
**Raspberry Pi é um COMPUTADOR COMPLETO do tamanho de um cartão de crédito.**

```
Tamanho: 8.5cm x 5.6cm (menor que seu celular)
Peso: 45 gramas
Preço: R$ 200-400 (dependendo do modelo)
```

### Comparação Visual:
```
┌─────────────────┐
│                 │
│  Raspberry Pi   │  ← Tamanho de um cartão de crédito
│                 │
│   [USB] [USB]   │
│   [HDMI] [Rede] │
└─────────────────┘
```

---

## 💻 É um Computador COMPLETO

### O Que Tem Dentro:
- ✅ **Processador** (CPU) - Quad-core 1.5 GHz
- ✅ **Memória RAM** - 2GB, 4GB ou 8GB
- ✅ **Wi-Fi** integrado
- ✅ **Bluetooth** integrado
- ✅ **Portas USB** (2 ou 4)
- ✅ **Porta HDMI** (conecta em TV/monitor)
- ✅ **Porta Ethernet** (cabo de rede)
- ✅ **40 pinos GPIO** (para sensores)

### O Que NÃO Tem:
- ❌ Disco rígido (usa cartão microSD)
- ❌ Teclado/mouse (conecta via USB)
- ❌ Monitor (conecta via HDMI)
- ❌ Case/gabinete (vende separado)

---

## 🎮 Modelos Disponíveis

### Raspberry Pi 4 (Recomendado para WiFiSense)

**Especificações:**
```
Processador: Quad-core ARM Cortex-A72 @ 1.5GHz
RAM: 2GB, 4GB ou 8GB
Wi-Fi: 802.11ac (5GHz)
Bluetooth: 5.0
USB: 2x USB 3.0 + 2x USB 2.0
Rede: Gigabit Ethernet
HDMI: 2x micro-HDMI (4K)
Preço: R$ 250-450
```

**Qual RAM escolher para WiFiSense:**
- 2GB: ✅ Suficiente (R$ 250)
- 4GB: ✅ Recomendado (R$ 350)
- 8GB: ⚠️ Desnecessário (R$ 450)

### Raspberry Pi 5 (Mais Novo - 2023)

**Especificações:**
```
Processador: Quad-core ARM Cortex-A76 @ 2.4GHz
RAM: 4GB ou 8GB
Wi-Fi: 802.11ac (5GHz)
Bluetooth: 5.0
USB: 2x USB 3.0 + 2x USB 2.0
Preço: R$ 400-600
```

**Vale a pena?**
- Para WiFiSense: ❌ Não necessário
- Raspberry Pi 4 é suficiente

### Raspberry Pi Zero 2 W (Mais Barato)

**Especificações:**
```
Processador: Quad-core ARM Cortex-A53 @ 1GHz
RAM: 512MB
Wi-Fi: 802.11n (2.4GHz)
Bluetooth: 4.2
USB: 1x micro-USB
Preço: R$ 80-120
```

**Vale a pena?**
- Para WiFiSense: ⚠️ Funciona mas limitado
- Recomendo Raspberry Pi 4

---

## 📦 O Que Você Precisa Comprar

### Kit Completo para WiFiSense:

#### 1. Raspberry Pi 4 (4GB RAM)
```
Preço: R$ 350
Onde: MercadoLivre, Amazon, FilipeFlop
```

#### 2. Cartão microSD (32GB ou 64GB)
```
Preço: R$ 30-50
Recomendado: SanDisk ou Kingston
Classe: 10 ou superior
```

#### 3. Fonte de Alimentação (5V 3A USB-C)
```
Preço: R$ 40-60
IMPORTANTE: Precisa ser 3A (não funciona com carregador de celular comum)
```

#### 4. Case/Gabinete (Opcional mas recomendado)
```
Preço: R$ 30-50
Protege o Raspberry Pi
```

#### 5. Cabo HDMI (Opcional - só para configuração inicial)
```
Preço: R$ 20-30
Tipo: micro-HDMI para HDMI
Só precisa para primeira configuração
```

**TOTAL: R$ 470-580**

---

## 🛒 Onde Comprar no Brasil

### Lojas Especializadas:
1. **FilipeFlop** - https://www.filipeflop.com
   - Especializada em Raspberry Pi
   - Entrega rápida
   - Suporte técnico

2. **Eletrogate** - https://www.eletrogate.com
   - Boa variedade
   - Preços competitivos

3. **Baú da Eletrônica** - https://www.baudaeletronica.com.br
   - Loja física em SP
   - Venda online

### Marketplaces:
4. **MercadoLivre**
   - Vários vendedores
   - Compare preços
   - Cuidado com falsificações

5. **Amazon Brasil**
   - Entrega rápida (Prime)
   - Garantia

---

## 💾 Como Instalar Seu Software

### Opção 1: Imagem Pronta (Mais Fácil)

**Você cria uma imagem com tudo instalado:**

```
1. Configurar Raspberry Pi uma vez
2. Instalar seu software WiFiSense
3. Configurar para iniciar automaticamente
4. Criar imagem do cartão SD
5. Clonar para outros cartões
```

**Vantagem:**
- ✅ Instala em 5 minutos (só gravar cartão)
- ✅ Sempre igual (padronizado)
- ✅ Fácil de escalar

**Como fazer:**
```bash
# No seu computador
# 1. Gravar imagem no cartão SD
sudo dd if=wifisense.img of=/dev/sdX bs=4M

# 2. Inserir no Raspberry Pi
# 3. Ligar
# 4. Pronto! Sistema funcionando
```

### Opção 2: Script de Instalação

**Você cria um script que instala tudo:**

```bash
#!/bin/bash
# install_wifisense.sh

# Atualiza sistema
sudo apt update
sudo apt upgrade -y

# Instala dependências
sudo apt install -y python3 python3-pip postgresql

# Instala seu software
cd /opt
sudo git clone https://github.com/seu-usuario/wifisense.git
cd wifisense
sudo pip3 install -r requirements.txt

# Configura para iniciar automaticamente
sudo systemctl enable wifisense
sudo systemctl start wifisense

echo "✅ WiFiSense instalado com sucesso!"
```

**Vantagem:**
- ✅ Sempre atualizado
- ✅ Fácil de manter
- ✅ Customizável

---

## 🚀 Modelo de Negócio com Raspberry Pi

### Modelo 1: Você Fornece o Hardware (Comodato)

**Como funciona:**
```
1. Você compra Raspberry Pi (R$ 350)
2. Instala seu software
3. Leva na casa do cliente
4. Cliente paga mensalidade
5. Se cancelar, você pega de volta
```

**Financeiro:**
```
Investimento: R$ 350 por cliente
Mensalidade: R$ 99/mês
Payback: 4 meses
Lucro após 1 ano: R$ 838 por cliente
```

**Vantagens:**
- ✅ Cliente não precisa comprar nada
- ✅ Você controla o hardware
- ✅ Fácil de recuperar se cancelar
- ✅ Pode reutilizar em outro cliente

**Desvantagens:**
- ❌ Investimento inicial alto
- ❌ Risco de perda/dano

### Modelo 2: Cliente Compra o Hardware

**Como funciona:**
```
1. Cliente compra Raspberry Pi (R$ 350)
2. Você instala seu software
3. Cliente paga mensalidade menor
4. Hardware é do cliente
```

**Financeiro:**
```
Cliente paga: R$ 350 (uma vez) + R$ 49/mês
Seu lucro: R$ 39/mês (sem custo de hardware)
```

**Vantagens:**
- ✅ Sem investimento inicial
- ✅ Sem risco de perda
- ✅ Escalável rapidamente

**Desvantagens:**
- ❌ Mensalidade menor
- ❌ Cliente pode cancelar e ficar com hardware

### Modelo 3: Híbrido (Recomendado)

**Como funciona:**
```
Plano Básico: R$ 99/mês (você fornece hardware)
Plano Econômico: R$ 49/mês (cliente compra hardware)
```

**Vantagens:**
- ✅ Cliente escolhe o que prefere
- ✅ Você atende diferentes perfis
- ✅ Maximiza receita

---

## 🔧 Configuração Técnica

### Sistema Operacional:

**Raspberry Pi OS (Recomendado)**
```
Baseado em: Debian Linux
Interface: Desktop ou Lite (sem interface)
Tamanho: 2-4 GB
```

**Para WiFiSense, use:**
- Raspberry Pi OS Lite (sem interface)
- Mais leve
- Menos consumo de recursos

### Instalação do WiFiSense:

```bash
# 1. Atualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Python e dependências
sudo apt install -y python3 python3-pip postgresql git

# 3. Clonar seu repositório
cd /opt
sudo git clone https://github.com/seu-usuario/wifisense.git
cd wifisense

# 4. Instalar dependências Python
sudo pip3 install -r requirements.txt

# 5. Configurar banco de dados
sudo -u postgres psql -f setup_postgresql.sql

# 6. Criar serviço systemd
sudo nano /etc/systemd/system/wifisense.service
```

**Arquivo wifisense.service:**
```ini
[Unit]
Description=WiFiSense Monitoring Service
After=network.target postgresql.service

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/wifisense/backend
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Ativar serviço:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable wifisense
sudo systemctl start wifisense
```

---

## 📊 Consumo e Custos

### Consumo de Energia:

**Raspberry Pi 4:**
```
Consumo: 5W (máximo 15W com periféricos)
Custo mensal: R$ 3-5 (24/7 ligado)
Custo anual: R$ 36-60
```

**Comparação:**
```
Raspberry Pi: R$ 5/mês
PC Desktop: R$ 50-100/mês
Notebook: R$ 20-40/mês
```

### Durabilidade:

**Vida útil:**
```
Raspberry Pi: 5-10 anos
Cartão SD: 2-5 anos (substituir periodicamente)
Fonte: 3-5 anos
```

---

## 🎯 Vantagens do Raspberry Pi para WiFiSense

### 1. Tamanho Compacto
```
✅ Cabe em qualquer lugar
✅ Discreto (cliente nem percebe)
✅ Fácil de transportar
```

### 2. Baixo Consumo
```
✅ R$ 5/mês de energia
✅ Pode ficar ligado 24/7
✅ Não esquenta
✅ Silencioso (sem ventilador)
```

### 3. Preço Acessível
```
✅ R$ 350 (hardware completo)
✅ Payback em 4 meses
✅ Reutilizável
```

### 4. Fácil de Gerenciar
```
✅ Acesso remoto (SSH)
✅ Atualização remota
✅ Reinicialização remota
✅ Monitoramento remoto
```

### 5. Confiável
```
✅ Linux estável
✅ Sem vírus
✅ Sem atualizações do Windows
✅ Funciona anos sem problemas
```

---

## 🔐 Acesso Remoto

### SSH (Linha de Comando):
```bash
# Do seu computador
ssh pi@192.168.1.100

# Comandos úteis
sudo systemctl status wifisense  # Ver status
sudo systemctl restart wifisense # Reiniciar
sudo reboot                      # Reiniciar Raspberry Pi
```

### VNC (Interface Gráfica):
```
1. Instalar VNC Server no Raspberry Pi
2. Conectar via VNC Viewer
3. Ver desktop remotamente
```

### Web Dashboard:
```
http://192.168.1.100:8000
```

---

## 📋 Checklist de Instalação

### Preparação:
- [ ] Raspberry Pi 4 (4GB)
- [ ] Cartão microSD (32GB)
- [ ] Fonte 5V 3A USB-C
- [ ] Case/gabinete
- [ ] Cabo ethernet (opcional)

### Software:
- [ ] Raspberry Pi OS instalado
- [ ] WiFiSense instalado
- [ ] PostgreSQL configurado
- [ ] Serviço systemd criado
- [ ] Inicialização automática ativada

### Configuração:
- [ ] Wi-Fi configurado
- [ ] IP fixo configurado
- [ ] SSH habilitado
- [ ] Telegram configurado
- [ ] Teste de movimento realizado

### Cliente:
- [ ] Raspberry Pi instalado na casa
- [ ] Conectado na tomada
- [ ] Conectado no Wi-Fi
- [ ] Cliente recebeu alerta de teste
- [ ] Treinamento concluído

---

## 🎉 Resumo Final

### O Que É Raspberry Pi:
```
✅ Computador completo
✅ Tamanho de um cartão
✅ R$ 350 (kit completo)
✅ Consome R$ 5/mês de energia
✅ Perfeito para WiFiSense
```

### Como Usar no Seu Negócio:
```
1. Comprar Raspberry Pi (R$ 350)
2. Instalar seu software
3. Levar na casa do cliente
4. Cobrar R$ 99/mês
5. Lucrar R$ 89/mês após 4 meses
```

### Vantagens:
```
✅ Pequeno e discreto
✅ Baixo consumo
✅ Confiável
✅ Fácil de gerenciar remotamente
✅ Reutilizável
```

---

**Raspberry Pi é a solução PERFEITA para WiFiSense!** 🚀

Pequeno, barato, confiável e fácil de gerenciar. Ideal para instalar na casa dos clientes e cobrar mensalidade.
