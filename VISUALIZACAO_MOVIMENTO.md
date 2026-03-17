# 🎨 Visualização de Movimento por Ondas Wi-Fi

## 🎉 NOVA FUNCIONALIDADE IMPLEMENTADA!

Adicionamos uma **visualização em tempo real** que mostra o movimento detectado pelas ondas Wi-Fi, tipo um "radar" ou "sonar"!

---

## 📺 O Que É?

Um componente visual que representa graficamente:
- **Presença detectada** (blob central)
- **Intensidade do movimento** (tamanho e cor)
- **Ondas de propagação** (quando há movimento)
- **Dispersão do sinal** (partículas ao redor)
- **Força do sinal RSSI** (barra lateral)

---

## 🎨 Como Funciona?

### Elementos Visuais

#### 1. Círculos Concêntricos (Ondas Wi-Fi)
- Representam as ondas de rádio do Wi-Fi
- Cor muda conforme o evento detectado
- Efeito visual de propagação

#### 2. Blob Central (Presença)
- **Tamanho**: Proporcional à energia do sinal
- **Cor**: Baseada no tipo de evento
  - 🔵 Azul = Parado
  - 🟢 Verde = Movimento
  - 🔴 Vermelho = Queda
  - ⚪ Cinza = Sem presença
- **Pulso**: Anima quando há movimento

#### 3. Ondas de Movimento
- Aparecem quando há movimento ativo
- Propagam do centro para fora
- Intensidade baseada na variação do sinal

#### 4. Partículas de Dispersão
- Aparecem quando há alta variância
- Representam instabilidade do ambiente
- Giram ao redor do centro

#### 5. Barra de RSSI
- Canto superior direito
- Mostra força do sinal em dBm
- Atualiza em tempo real

---

## 🎮 Como Ver

### Acesse o Dashboard
```
http://localhost:5173
```

### Localização
- **Página**: Dashboard
- **Posição**: Lado direito, abaixo dos controles
- **Ao lado**: Gráfico de sinal

### O Que Observar

✅ **Sem Presença**
- Blob pequeno e cinza
- Ondas sutis
- Texto: "SEM PRESENÇA"

✅ **Pessoa Parada**
- Blob médio e azul
- Pulso leve
- Texto: "PARADO"

✅ **Pessoa em Movimento**
- Blob grande e verde
- Ondas propagando
- Partículas girando
- Texto: "MOVIMENTO"

✅ **Queda Detectada**
- Blob vermelho intenso
- Ondas rápidas
- Texto: "QUEDA!"

---

## 🧪 Teste Agora!

### 1. Inicie o Monitoramento
- Clique em "Iniciar Monitoramento"
- Observe o radar aparecer

### 2. Fique Parado
- Blob azul pequeno
- Pulso suave
- Poucas partículas

### 3. Ande pela Sala
- Blob verde cresce
- Ondas se propagam
- Partículas aparecem
- Animação mais intensa

### 4. Aproxime-se do Roteador
- RSSI aumenta (barra lateral)
- Blob fica maior
- Mais energia visual

### 5. Afaste-se do Roteador
- RSSI diminui
- Blob fica menor
- Menos energia visual

---

## 🎨 Cores e Significados

| Cor | Evento | Significado |
|-----|--------|-------------|
| ⚪ Cinza | Sem Presença | Ambiente vazio |
| 🔵 Azul | Parado | Presença detectada, sem movimento |
| 🟢 Verde | Movimento | Movimento ativo detectado |
| 🔴 Vermelho | Queda | Evento crítico - queda suspeita |
| 🟡 Amarelo | Inatividade | Sem movimento por muito tempo |

---

## 📊 Métricas Visualizadas

### Energia do Sinal
- **Fonte**: `signal_energy` das features
- **Efeito**: Tamanho do blob central
- **Range**: 0-20 (normalizado para 0-1)

### Variância do Sinal
- **Fonte**: `signal_variance` das features
- **Efeito**: Número de partículas
- **Range**: 0-5 (normalizado para 0-1)

### RSSI
- **Fonte**: `rssi` do sinal
- **Efeito**: Barra lateral
- **Range**: -100 a -30 dBm

### Taxa de Variação
- **Fonte**: `rate_of_change` das features
- **Efeito**: Velocidade das ondas
- **Uso**: Detectar movimento brusco

---

## 🔧 Arquivos Criados

### Frontend
- **`frontend/src/components/WifiRadar.tsx`**
  - Componente React com canvas
  - Animação em 20 FPS
  - Renderização baseada em features

### CSS
- **`frontend/src/index.css`** (adicionado)
  - Estilos do radar
  - Legenda de cores
  - Layout responsivo

### Dashboard
- **`frontend/src/pages/Dashboard.tsx`** (modificado)
  - Radar adicionado ao layout
  - Grid ajustado para 2 colunas

---

## 🎯 Diferencial

### Antes
- ✅ Gráfico de linha (RSSI, energia, variância)
- ✅ Timeline de eventos
- ❌ Sem visualização espacial

### Agora
- ✅ Gráfico de linha
- ✅ Timeline de eventos
- ✅ **Radar visual de movimento** 🎨
- ✅ Representação espacial
- ✅ Animação em tempo real
- ✅ Feedback visual imediato

---

## 🚀 Tecnologias Usadas

### Canvas API
- Renderização 2D de alta performance
- Animações suaves
- Efeitos visuais complexos

### React Hooks
- `useRef` para acesso ao canvas
- `useEffect` para animação
- `useStore` para dados em tempo real

### Zustand Store
- Estado global reativo
- Atualização automática
- Performance otimizada

---

## 🎨 Inspiração

Este tipo de visualização é inspirado em:
- **Sistemas de radar** militares
- **Sonar** de submarinos
- **Visualizadores de áudio**
- **Pesquisas acadêmicas** de Wi-Fi sensing

Exemplos de papers:
- "WiFall: Device-free Fall Detection" (INFOCOM 2014)
- "E-eyes: Device-free Location-oriented Activity" (MobiCom 2014)
- "FIFS: Fine-grained Indoor Fingerprinting" (MobiCom 2012)

---

## 🔮 Melhorias Futuras

### Possíveis Adições

1. **Mapa 2D do Ambiente**
   - Desenhar planta do cômodo
   - Posicionar pessoa detectada
   - Trajetória de movimento

2. **Múltiplas Pessoas**
   - Vários blobs
   - Cores diferentes
   - Tracking individual

3. **Heatmap Temporal**
   - Áreas mais frequentadas
   - Padrões de movimento
   - Histórico visual

4. **Modo 3D**
   - Visualização tridimensional
   - Rotação interativa
   - Profundidade do sinal

5. **Gestos Detectados**
   - Padrões específicos
   - Ações reconhecidas
   - Comandos por movimento

---

## 📝 Código Técnico

### Estrutura do Canvas

```typescript
// Círculos concêntricos (ondas)
for (let i = 0; i < 5; i++) {
  ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
  ctx.stroke();
}

// Blob central (presença)
const gradient = ctx.createRadialGradient(...);
ctx.arc(centerX, centerY, blobRadius, 0, Math.PI * 2);
ctx.fill();

// Ondas de movimento
if (movimento) {
  for (let i = 0; i < 3; i++) {
    const waveRadius = blobRadius + wavePhase * 80;
    ctx.arc(centerX, centerY, waveRadius, 0, Math.PI * 2);
    ctx.stroke();
  }
}

// Partículas de dispersão
for (let i = 0; i < numParticles; i++) {
  const angle = (Math.PI * 2 * i) / numParticles;
  ctx.arc(x, y, size, 0, Math.PI * 2);
  ctx.fill();
}
```

### Animação

```typescript
useEffect(() => {
  const interval = setInterval(() => {
    // Re-render a cada 50ms (20 FPS)
    canvasRef.current?.getContext('2d');
  }, 50);
  
  return () => clearInterval(interval);
}, []);
```

---

## 🎉 Resultado

Agora você tem uma visualização **profissional** e **intuitiva** do movimento detectado por Wi-Fi!

**Características:**
- ✅ Atualização em tempo real
- ✅ Animações suaves
- ✅ Cores intuitivas
- ✅ Feedback visual imediato
- ✅ Design moderno
- ✅ Performance otimizada

**Acesse agora:**
```
http://localhost:5173
```

E veja o radar em ação! 🎨🎉

---

**Visualização desenvolvida com ❤️ usando Canvas API e React!**
