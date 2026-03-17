# 📝 Changelog - WiFiSense Local

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

---

## [1.0.0] - 2024-03-14

### 🎉 Lançamento Inicial

#### ✨ Funcionalidades Implementadas

**Backend (Python + FastAPI)**
- Sistema de monitoramento em tempo real com loop assíncrono
- Arquitetura modular em camadas (Capture → Processing → Detection)
- Provider de simulação com 6 modos diferentes
- Processamento de sinal com extração de 8 features
- Detector heurístico baseado em regras configuráveis
- API REST completa com 8 endpoints
- WebSocket para streaming de dados em tempo real
- Persistência em SQLite com SQLAlchemy
- Sistema de alertas para eventos críticos
- Configuração dinâmica de limiares e sensibilidade

**Frontend (React + TypeScript + Vite)**
- Dashboard interativo com atualização em tempo real
- 3 páginas principais: Dashboard, Histórico, Configurações
- 9 componentes reutilizáveis
- Gráficos em tempo real com Recharts
- Gerenciamento de estado com Zustand
- WebSocket client com auto-reconnect
- Dark theme profissional
- Interface responsiva
- Animações e transições suaves

**Detecção de Eventos**
- ✅ Sem Presença (ambiente vazio)
- ✅ Presença Parada (micro-movimentos)
- ✅ Presença em Movimento (movimento ativo)
- ✅ Queda Suspeita (pico brusco de sinal)
- ✅ Inatividade Prolongada (imobilidade)

**Modos de Simulação**
- 🏠 Ambiente Vazio
- 🧍 Pessoa Parada
- 🚶 Pessoa Andando
- 🤕 Queda Simulada
- 😴 Imobilidade Pós-Queda
- 🎲 Aleatório

**Configurações Ajustáveis**
- Sensibilidade de movimento (0.5 - 10.0)
- Limiar de queda (3.0 - 30.0)
- Tempo de inatividade (10 - 120 segundos)
- Intervalo de amostragem (0.1 - 2.0 segundos)
- Provider ativo (mock/rssi/csi)

**Documentação**
- 📖 README.md completo com instruções
- 🚀 GUIA_RAPIDO.md para início rápido
- 🏗️ ARQUITETURA.md com detalhes técnicos
- 🔌 INTEGRACAO_HARDWARE.md para hardware real

**Scripts e Ferramentas**
- `start_backend.bat` - Inicialização automática do backend
- `start_frontend.bat` - Inicialização automática do frontend
- `validate_system.py` - Script de validação completo

#### 🎯 Arquitetura

**Padrões de Design**
- Strategy Pattern (Providers e Detectores)
- Singleton Pattern (Services)
- Observer Pattern (WebSocket)
- Pipeline Pattern (Processamento)
- Repository Pattern (Database)

**Tecnologias**
- Backend: Python 3.10+, FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2.9
- Frontend: React 18, TypeScript 5.6, Vite 6.0, Zustand 5.0, Recharts 2.13
- Banco: SQLite 3
- Comunicação: WebSocket nativo, REST API

#### 📊 Métricas

- **Backend**: 12 módulos, ~1500 linhas de código
- **Frontend**: 15 componentes, ~1200 linhas de código
- **Documentação**: 4 arquivos, ~2000 linhas
- **Cobertura**: Estrutura completa e funcional

#### 🔮 Preparado para Futuro

**Placeholders Implementados**
- `rssi_placeholder.py` - Pronto para integração RSSI real
- `csi_placeholder.py` - Pronto para integração CSI real
- `DetectorBase` - Interface para modelos ML
- `AlertService` - Estrutura para alertas externos

**Hardware Suportado (Futuro)**
- Intel 5300 NIC (CSI)
- ESP32-S3 (CSI)
- Atheros AR9271 (CSI)
- Qualquer adaptador Wi-Fi (RSSI)

**Integrações Planejadas**
- Machine Learning (Random Forest, LSTM, CNN)
- WhatsApp Business API
- Twilio SMS
- Firebase Push Notifications
- Telegram Bot

#### 🐛 Problemas Conhecidos

Nenhum problema crítico identificado na versão inicial.

#### 📝 Notas

- Sistema testado em Windows 10/11
- Requer Python 3.10+ e Node.js 18+
- Primeira versão focada em simulação
- Hardware real requer configuração adicional

---

## [Futuro] - Roadmap

### [1.1.0] - Planejado

**Funcionalidades**
- [ ] Integração com RSSI real (Scapy/PyShark)
- [ ] Suporte a múltiplos providers simultâneos
- [ ] Exportação de dados (CSV, JSON)
- [ ] Gráficos adicionais (FFT, espectrograma)
- [ ] Modo de gravação de sessões

**Melhorias**
- [ ] Testes unitários (pytest)
- [ ] Testes de integração
- [ ] CI/CD com GitHub Actions
- [ ] Docker Compose
- [ ] Logs estruturados

### [1.2.0] - Planejado

**Funcionalidades**
- [ ] Integração com CSI real (Intel 5300)
- [ ] Detector baseado em ML
- [ ] Treinamento de modelos customizados
- [ ] API de plugins

**Melhorias**
- [ ] Performance otimizada
- [ ] Compressão de dados históricos
- [ ] Backup automático do banco
- [ ] Modo headless (sem UI)

### [2.0.0] - Planejado

**Funcionalidades**
- [ ] Alertas externos (WhatsApp, SMS, Push)
- [ ] Multi-room support
- [ ] Autenticação e usuários
- [ ] Dashboard web remoto
- [ ] Mobile app (React Native)

**Melhorias**
- [ ] Migração para PostgreSQL (opcional)
- [ ] Clustering e alta disponibilidade
- [ ] API GraphQL
- [ ] Documentação interativa

---

## Convenções

### Tipos de Mudanças
- `✨ Added` - Novas funcionalidades
- `🔧 Changed` - Mudanças em funcionalidades existentes
- `🐛 Fixed` - Correções de bugs
- `🗑️ Removed` - Funcionalidades removidas
- `⚠️ Deprecated` - Funcionalidades marcadas para remoção
- `🔒 Security` - Correções de segurança

### Versionamento Semântico
- **MAJOR** (X.0.0) - Mudanças incompatíveis na API
- **MINOR** (0.X.0) - Novas funcionalidades compatíveis
- **PATCH** (0.0.X) - Correções de bugs compatíveis

---

**Desenvolvido com ❤️ para monitoramento local de presença via Wi-Fi**
