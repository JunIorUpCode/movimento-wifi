# 📡 Guia: Como Capturar Sinais Wi-Fi Reais

## 🎯 Objetivo
Substituir os dados simulados por captura real de sinais Wi-Fi do seu computador.

---

## ⚡ MÉTODO 1: RSSI no Windows (RECOMENDADO)

### O Que É RSSI?
- **RSSI** = Received Signal Strength Indicator
- Mede a potência do sinal Wi-Fi em dBm
- Valores típicos: -30 dBm (muito forte) a -100 dBm (muito fraco)
- **Vantagem**: Funciona com qualquer adaptador Wi-Fi, sem hardware especial

### Passo 1: Testar Captura Real

Abra um terminal no backend e execute:

```bash
cd backend
.\venv\Scripts\python.exe test_real_wifi.py
```

**O que você deve ver:**
```
==============================================================
  TESTE DE CAPTURA DE SINAIS WI-FI REAIS
==============================================================

[1/3] Iniciando provider...
✓ Provider iniciado
  Interface: Wi-Fi
  Rede alvo: SuaRedeWiFi

[2/3] Capturando sinais (10 amostras)...
--------------------------------------------------------------
Amostra  1: RSSI = -45.30 dBm | Timestamp = 1234567890.12
Amostra  2: RSSI = -46.10 dBm | Timestamp = 1234567891.13
Amostra  3: RSSI = -44.80 dBm | Timestamp = 1234567892.14
...
```

**✅ Se funcionou:** Você verá valores de RSSI variando entre -30 e -90 dBm

**❌ Se deu erro:** Veja seção "Troubleshooting" abaixo

---

### Passo 2: Integrar no Sistema

Agora vamos fazer o sistema usar a captura real em vez do mock.

**Edite o arquivo:** `backend/app/services/monitor_service.py`

**Encontre esta linha (linha ~40):**
```python
self._provider: SignalProvider = MockSignalProvider()
```

**Substitua por:**
```python
from app.capture.rssi_windows import RssiWindowsProvider
# ...
self._provider: SignalProvider = RssiWindowsProvider()
```

**Arquivo completo ficará assim:**
```python
# No topo do arquivo, adicione o import
from app.capture.rssi_windows import RssiWindowsProvider

# ... resto dos imports ...

class MonitorService:
    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        # MUDANÇA AQUI: Troca Mock por Windows RSSI
        self._provider: SignalProvider = RssiWindowsProvider()
        
        # Resto do código continua igual
        self._processor = SignalProcessor()
        self._detector = HeuristicDetector()
        # ...
```

---

### Passo 3: Reiniciar o Backend

1. **Pare o backend atual** (Ctrl+C no terminal)
2. **Inicie novamente:**
   ```bash
   .\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Verifique os logs:**
   ```
   [RssiWindowsProvider] Interface detectada: Wi-Fi
   [RssiWindowsProvider] Monitorando rede: SuaRedeWiFi
   ```

---

### Passo 4: Testar no Dashboard

1. Abra http://localhost:5173
2. Clique em "Iniciar Monitoramento"
3. **Agora os dados são REAIS!**

**Como testar se está funcionando:**

✅ **Teste 1: Aproxime-se do roteador**
- Ande em direção ao seu roteador Wi-Fi
- O RSSI deve aumentar (ficar menos negativo)
- Ex: -60 dBm → -45 dBm

✅ **Teste 2: Afaste-se do roteador**
- Ande para longe do roteador
- O RSSI deve diminuir (ficar mais negativo)
- Ex: -45 dBm → -70 dBm

✅ **Teste 3: Movimento**
- Ande pela sala
- O gráfico deve mostrar variações
- Sistema deve detectar "Presença (Movendo)"

✅ **Teste 4: Fique parado**
- Pare de se mover
- Após alguns segundos: "Presença (Parado)"

---

## 🎛️ Ajustar Sensibilidade

Com dados reais, você provavelmente precisará ajustar os limiares:

### No Dashboard:
1. Vá em "Configurações"
2. Ajuste:
   - **Sensibilidade de Movimento**: Comece com 1.0 (mais sensível)
   - **Limiar de Queda**: Comece com 8.0
   - **Tempo de Inatividade**: 20 segundos
3. Clique em "Salvar"

### Por que ajustar?
- Sinais reais são mais sutis que simulados
- Cada ambiente é diferente
- Depende da distância do roteador

---

## 🔍 Entendendo os Valores RSSI

| RSSI (dBm) | Qualidade | O que significa |
|------------|-----------|-----------------|
| -30 a -50  | Excelente | Muito perto do roteador |
| -50 a -60  | Bom       | Distância normal |
| -60 a -70  | Regular   | Longe do roteador |
| -70 a -80  | Fraco     | Muito longe |
| -80 a -100 | Péssimo   | Quase sem sinal |

**Para detecção de presença:**
- Variações de 5-10 dBm = movimento sutil
- Variações de 10-20 dBm = movimento ativo
- Picos de 20+ dBm = movimento brusco (possível queda)

---

## 🚨 Troubleshooting

### Erro: "netsh não é reconhecido"
**Solução:** Você está no Windows? O netsh é nativo do Windows.

### Erro: "Nenhuma interface Wi-Fi encontrada"
**Solução:** 
1. Verifique se seu Wi-Fi está ligado
2. Execute: `netsh wlan show interfaces`
3. Deve mostrar sua interface Wi-Fi

### RSSI sempre -70 dBm (não varia)
**Possíveis causas:**
1. Não está conectado a nenhuma rede Wi-Fi
2. Adaptador Wi-Fi desligado
3. Windows não está atualizando os dados

**Solução:**
1. Conecte-se a uma rede Wi-Fi
2. Execute o teste novamente
3. Tente especificar o SSID manualmente:
   ```python
   self._provider = RssiWindowsProvider(target_ssid="NomeDaSuaRede")
   ```

### Sistema não detecta movimento
**Solução:**
1. Reduza "Sensibilidade de Movimento" para 0.5
2. Ande mais perto do roteador
3. Faça movimentos mais amplos

### Muitos falsos positivos
**Solução:**
1. Aumente "Sensibilidade de Movimento" para 3.0
2. Aumente "Limiar de Queda" para 15.0
3. Ambiente com muita interferência? Considere CSI (mais preciso)

---

## 📊 Limitações do RSSI

### Vantagens ✅
- Funciona com qualquer adaptador Wi-Fi
- Não precisa hardware especial
- Fácil de implementar
- Funciona no Windows sem drivers especiais

### Limitações ❌
- Menos preciso que CSI
- Afetado por interferências
- Não distingue bem múltiplas pessoas
- Sensível a obstáculos (paredes, móveis)

### Quando usar RSSI?
- ✅ Detecção básica de presença
- ✅ Monitoramento de um cômodo
- ✅ Prototipagem e testes
- ✅ Não quer comprar hardware especial

### Quando usar CSI? (mais avançado)
- ✅ Detecção precisa de movimento
- ✅ Múltiplas pessoas
- ✅ Gestos e atividades específicas
- ✅ Pesquisa acadêmica
- ❌ Requer hardware especial (Intel 5300, ESP32-S3)

---

## 🔮 Próximos Passos

### Opção 1: Melhorar RSSI
1. Coletar dados de calibração
2. Treinar modelo de Machine Learning
3. Ajustar limiares por ambiente

### Opção 2: Migrar para CSI
1. Comprar hardware CSI (ESP32-S3 ~R$50)
2. Seguir guia em `INTEGRACAO_HARDWARE.md`
3. Obter precisão 10x maior

### Opção 3: Múltiplos Roteadores
1. Usar vários pontos de acesso
2. Triangulação de sinal
3. Melhor cobertura

---

## 📝 Checklist de Integração

- [ ] Executei `test_real_wifi.py` com sucesso
- [ ] Vi valores de RSSI variando
- [ ] Editei `monitor_service.py`
- [ ] Reiniciei o backend
- [ ] Testei movimento no dashboard
- [ ] Ajustei sensibilidade nas configurações
- [ ] Sistema detecta presença real
- [ ] Sistema detecta movimento real

---

## 🎉 Parabéns!

Se chegou até aqui, você agora tem um sistema de monitoramento de presença **REAL** usando sinais Wi-Fi!

**O que mudou:**
- ❌ Antes: Dados simulados (fake)
- ✅ Agora: Dados reais do seu Wi-Fi

**O que você pode fazer:**
- Detectar quando alguém entra/sai do cômodo
- Monitorar movimento em tempo real
- Detectar quedas (com calibração)
- Alertar inatividade prolongada

---

**Dúvidas? Veja `INTEGRACAO_HARDWARE.md` para opções mais avançadas!**
