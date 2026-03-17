# 🏗️ Arquitetura Multi-Tenant - Telegram (Opção 1)

## 📋 Visão Geral

**Estratégia**: Um bot do Telegram por família/idoso

Cada família cria seu próprio bot no Telegram, garantindo:
- ✅ Privacidade total
- ✅ Personalização completa
- ✅ Escalabilidade ilimitada
- ✅ Gratuito para todos
- ✅ Sem limites de mensagens

---

## 🗄️ Estrutura do Banco de Dados

### 1. Tabelas Necessárias

```sql
-- Tabela de usuários do SaaS
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'admin', 'caregiver', 'family'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Tabela de idosos monitorados
CREATE TABLE elderly (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    birth_date DATE,
    address TEXT,
    notes TEXT,
    owner_user_id INTEGER REFERENCES users(id),  -- Cuidador principal
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tabela de configuração Telegram (POR IDOSO)
CREATE TABLE telegram_configs (
    id SERIAL PRIMARY KEY,
    elderly_id INTEGER UNIQUE REFERENCES elderly(id) ON DELETE CASCADE,
    bot_token VARCHAR(200) NOT NULL,
    bot_username VARCHAR(100),
    chat_ids TEXT[] NOT NULL DEFAULT '{}',  -- Array de chat IDs
    enabled BOOLEAN DEFAULT TRUE,
    min_confidence FLOAT DEFAULT 0.7,
    cooldown_seconds INTEGER DEFAULT 300,
    quiet_hours_start INTEGER,  -- Hora de início (0-23)
    quiet_hours_end INTEGER,    -- Hora de fim (0-23)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Tabela de cuidadores autorizados por idoso
CREATE TABLE elderly_caregivers (
    id SERIAL PRIMARY KEY,
    elderly_id INTEGER REFERENCES elderly(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    chat_id VARCHAR(50),  -- Chat ID do Telegram deste cuidador
    relationship VARCHAR(50),  -- 'filho', 'filha', 'enfermeiro', etc.
    can_configure BOOLEAN DEFAULT FALSE,  -- Pode alterar configurações
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(elderly_id, user_id)
);

-- Índices para performance
CREATE INDEX idx_elderly_owner ON elderly(owner_user_id);
CREATE INDEX idx_telegram_configs_elderly ON telegram_configs(elderly_id);
CREATE INDEX idx_elderly_caregivers_elderly ON elderly_caregivers(elderly_id);
CREATE INDEX idx_elderly_caregivers_user ON elderly_caregivers(user_id);
```

---

## 🔌 Endpoints da API

### 1. Gerenciamento de Idosos

#### Criar Idoso
```http
POST /api/elderly
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "João Silva",
  "birth_date": "1950-05-15",
  "address": "Rua das Flores, 123",
  "notes": "Diabético, toma remédio às 8h"
}

Response 201:
{
  "id": 1,
  "name": "João Silva",
  "owner_user_id": 5,
  "created_at": "2026-03-14T18:00:00Z"
}
```

#### Listar Idosos do Usuário
```http
GET /api/elderly
Authorization: Bearer {token}

Response 200:
[
  {
    "id": 1,
    "name": "João Silva",
    "birth_date": "1950-05-15",
    "is_active": true,
    "telegram_configured": true,
    "caregivers_count": 3
  }
]
```

---

### 2. Configuração do Telegram

#### Obter Guia de Setup
```http
GET /api/elderly/{elderly_id}/telegram/setup-guide
Authorization: Bearer {token}

Response 200:
{
  "steps": [
    {
      "step": 1,
      "title": "Abrir o Telegram",
      "description": "Abra o aplicativo Telegram no seu celular ou computador"
    },
    {
      "step": 2,
      "title": "Encontrar o BotFather",
      "description": "Na busca, digite: @BotFather",
      "image_url": "/assets/botfather.png"
    },
    {
      "step": 3,
      "title": "Criar o Bot",
      "description": "Digite: /newbot",
      "example": "/newbot"
    },
    {
      "step": 4,
      "title": "Nome do Bot",
      "description": "Escolha um nome (ex: João Silva Alertas)",
      "example": "João Silva Alertas"
    },
    {
      "step": 5,
      "title": "Username do Bot",
      "description": "Escolha um username terminando com 'bot'",
      "example": "joao_silva_alertas_bot"
    },
    {
      "step": 6,
      "title": "Copiar o Token",
      "description": "O BotFather vai te dar um TOKEN. Copie-o!",
      "example": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    }
  ],
  "video_tutorial_url": "https://youtu.be/example"
}
```

#### Configurar Telegram
```http
POST /api/elderly/{elderly_id}/telegram/config
Authorization: Bearer {token}
Content-Type: application/json

{
  "bot_token": "8462799481:AAGUfH7OTOfCvN4ppDIY4VA8FGZ6lYSBpmA",
  "bot_username": "joao_silva_bot",
  "min_confidence": 0.7,
  "cooldown_seconds": 300,
  "quiet_hours_start": 22,
  "quiet_hours_end": 7
}

Response 201:
{
  "id": 1,
  "elderly_id": 1,
  "bot_username": "joao_silva_bot",
  "enabled": true,
  "chat_ids": [],
  "message": "Configuração salva! Agora adicione os cuidadores."
}
```

#### Obter Chat ID do Usuário
```http
GET /api/telegram/my-chat-id
Authorization: Bearer {token}

Response 200:
{
  "instructions": "Envie /start para o bot @joao_silva_bot e depois clique em 'Verificar'",
  "bot_username": "joao_silva_bot",
  "check_url": "/api/elderly/1/telegram/check-chat-id"
}
```

#### Verificar e Adicionar Chat ID
```http
POST /api/elderly/{elderly_id}/telegram/add-caregiver
Authorization: Bearer {token}
Content-Type: application/json

{
  "relationship": "filho"
}

Response 200:
{
  "chat_id": "2085218769",
  "added": true,
  "message": "Chat ID adicionado com sucesso!"
}
```

#### Adicionar Outro Cuidador
```http
POST /api/elderly/{elderly_id}/telegram/add-caregiver-manual
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": 10,
  "chat_id": "987654321",
  "relationship": "enfermeira"
}

Response 200:
{
  "added": true,
  "total_caregivers": 2
}
```

#### Listar Cuidadores
```http
GET /api/elderly/{elderly_id}/caregivers
Authorization: Bearer {token}

Response 200:
[
  {
    "user_id": 5,
    "name": "Maria Silva",
    "chat_id": "2085218769",
    "relationship": "filha",
    "can_configure": true,
    "is_owner": true
  },
  {
    "user_id": 10,
    "name": "Ana Costa",
    "chat_id": "987654321",
    "relationship": "enfermeira",
    "can_configure": false,
    "is_owner": false
  }
]
```

#### Testar Notificação
```http
POST /api/elderly/{elderly_id}/telegram/test
Authorization: Bearer {token}

Response 200:
{
  "sent": true,
  "recipients": 2,
  "message": "Mensagem de teste enviada para 2 cuidadores"
}
```

---

## 💻 Implementação Backend

### 1. Serviço de Notificação Multi-Tenant

```python
# app/services/multi_tenant_notification_service.py

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import TelegramConfig, ElderlyCaregivers
from app.services.notification_service import NotificationService
from app.services.notification_types import Alert, NotificationConfig


class MultiTenantNotificationService:
    """Serviço de notificações multi-tenant."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def send_alert_to_elderly(
        self, 
        elderly_id: int, 
        alert: Alert
    ) -> bool:
        """
        Envia alerta para todos os cuidadores de um idoso específico.
        
        Args:
            elderly_id: ID do idoso
            alert: Alerta a ser enviado
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        # Busca configuração do Telegram deste idoso
        result = await self.db.execute(
            select(TelegramConfig).where(
                TelegramConfig.elderly_id == elderly_id,
                TelegramConfig.enabled == True
            )
        )
        config = result.scalar_one_or_none()
        
        if not config:
            logger.warning(f"No Telegram config for elderly {elderly_id}")
            return False
        
        if not config.chat_ids:
            logger.warning(f"No chat IDs configured for elderly {elderly_id}")
            return False
        
        # Cria configuração de notificação com o bot desta família
        notification_config = NotificationConfig(
            enabled=True,
            channels=["telegram"],
            telegram_bot_token=config.bot_token,
            telegram_chat_ids=config.chat_ids,
            min_confidence=config.min_confidence,
            cooldown_seconds=config.cooldown_seconds,
            quiet_hours=[(config.quiet_hours_start, config.quiet_hours_end)] 
                if config.quiet_hours_start is not None else []
        )
        
        # Cria serviço de notificação
        service = NotificationService(notification_config)
        
        # Envia alerta
        try:
            await service.send_alert(alert)
            logger.info(
                f"Alert sent to elderly {elderly_id}: "
                f"{len(config.chat_ids)} recipients"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending alert to elderly {elderly_id}: {e}")
            return False
    
    async def get_telegram_config(
        self, 
        elderly_id: int
    ) -> Optional[TelegramConfig]:
        """Obtém configuração do Telegram de um idoso."""
        result = await self.db.execute(
            select(TelegramConfig).where(
                TelegramConfig.elderly_id == elderly_id
            )
        )
        return result.scalar_one_or_none()
    
    async def add_caregiver_chat_id(
        self,
        elderly_id: int,
        chat_id: str
    ) -> bool:
        """Adiciona chat ID de um cuidador."""
        config = await self.get_telegram_config(elderly_id)
        
        if not config:
            return False
        
        # Adiciona chat_id se não existir
        if chat_id not in config.chat_ids:
            config.chat_ids.append(chat_id)
            await self.db.commit()
            logger.info(f"Chat ID {chat_id} added to elderly {elderly_id}")
        
        return True
    
    async def remove_caregiver_chat_id(
        self,
        elderly_id: int,
        chat_id: str
    ) -> bool:
        """Remove chat ID de um cuidador."""
        config = await self.get_telegram_config(elderly_id)
        
        if not config:
            return False
        
        # Remove chat_id se existir
        if chat_id in config.chat_ids:
            config.chat_ids.remove(chat_id)
            await self.db.commit()
            logger.info(f"Chat ID {chat_id} removed from elderly {elderly_id}")
        
        return True
```

### 2. Integração com Detecção de Eventos

```python
# app/services/monitor_service.py

async def _handle_event_detected(self, event_type: str, confidence: float):
    """Processa evento detectado e envia notificações."""
    
    # ... código existente ...
    
    # Envia notificação para o idoso específico
    if self.current_elderly_id:
        multi_tenant_service = MultiTenantNotificationService(self.db)
        
        alert = Alert(
            event_type=event_type,
            confidence=confidence,
            timestamp=time.time(),
            message=self._format_alert_message(event_type, confidence),
            details={
                "rssi": current_rssi,
                "variance": variance,
                "elderly_id": self.current_elderly_id
            }
        )
        
        await multi_tenant_service.send_alert_to_elderly(
            self.current_elderly_id,
            alert
        )
```

---

## 🎨 Interface do Usuário (Frontend)

### 1. Tela de Configuração do Telegram

```typescript
// frontend/src/pages/TelegramSetup.tsx

interface TelegramSetupProps {
  elderlyId: number;
}

export function TelegramSetup({ elderlyId }: TelegramSetupProps) {
  const [step, setStep] = useState(1);
  const [botToken, setBotToken] = useState('');
  const [botUsername, setBotUsername] = useState('');
  const [chatId, setChatId] = useState('');
  
  const handleSaveConfig = async () => {
    await api.post(`/elderly/${elderlyId}/telegram/config`, {
      bot_token: botToken,
      bot_username: botUsername
    });
    
    setStep(2); // Próximo passo: adicionar cuidadores
  };
  
  const handleAddChatId = async () => {
    await api.post(`/elderly/${elderlyId}/telegram/add-caregiver`);
    // Sistema detecta automaticamente o chat_id
  };
  
  return (
    <div className="telegram-setup">
      {step === 1 && (
        <SetupGuide onComplete={() => setStep(2)} />
      )}
      
      {step === 2 && (
        <ConfigForm
          botToken={botToken}
          setBotToken={setBotToken}
          botUsername={botUsername}
          setBotUsername={setBotUsername}
          onSave={handleSaveConfig}
        />
      )}
      
      {step === 3 && (
        <AddCaregivers
          elderlyId={elderlyId}
          onComplete={() => setStep(4)}
        />
      )}
      
      {step === 4 && (
        <TestNotification elderlyId={elderlyId} />
      )}
    </div>
  );
}
```

---

## 📱 Fluxo do Usuário Final

### Passo 1: Cadastro do Idoso
1. Cuidador faz login no SaaS
2. Clica em "Adicionar Idoso"
3. Preenche dados (nome, data nascimento, etc.)
4. Sistema cria registro no banco

### Passo 2: Configurar Telegram
1. Sistema mostra: "Configure as notificações"
2. Cuidador clica em "Configurar Telegram"
3. Sistema mostra tutorial passo a passo
4. Cuidador cria bot no Telegram (2 minutos)
5. Cuidador cola o token no sistema
6. Sistema valida e salva

### Passo 3: Adicionar Cuidadores
1. Sistema mostra: "Adicione os cuidadores"
2. Cuidador principal envia /start para o bot
3. Sistema detecta chat_id automaticamente
4. Cuidador adiciona outros familiares:
   - Envia link do bot para familiar
   - Familiar dá /start no bot
   - Sistema detecta e adiciona automaticamente

### Passo 4: Testar
1. Sistema oferece: "Enviar mensagem de teste"
2. Cuidador clica em "Testar"
3. Todos os cuidadores recebem mensagem
4. Configuração concluída! ✅

---

## 🔒 Segurança e Privacidade

### 1. Isolamento de Dados
- Cada família tem seu próprio bot
- Tokens criptografados no banco
- Chat IDs não são compartilhados entre famílias

### 2. Controle de Acesso
```python
# Middleware de autorização
async def check_elderly_access(user_id: int, elderly_id: int) -> bool:
    """Verifica se usuário tem acesso ao idoso."""
    result = await db.execute(
        select(ElderlyCaregivers).where(
            ElderlyCaregivers.user_id == user_id,
            ElderlyCaregivers.elderly_id == elderly_id
        )
    )
    return result.scalar_one_or_none() is not None
```

### 3. Auditoria
```sql
-- Tabela de logs de acesso
CREATE TABLE access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    elderly_id INTEGER REFERENCES elderly(id),
    action VARCHAR(50),
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📊 Métricas e Monitoramento

### 1. Dashboard do Admin
- Total de idosos cadastrados
- Total de bots configurados
- Taxa de configuração (% de idosos com Telegram)
- Alertas enviados por dia
- Taxa de sucesso de envio

### 2. Dashboard do Cuidador
- Status do bot (ativo/inativo)
- Último alerta enviado
- Cuidadores cadastrados
- Histórico de alertas

---

## 🚀 Escalabilidade

### Limites do Telegram (por bot):
- ✅ 30 mensagens/segundo
- ✅ Ilimitado número de bots
- ✅ Ilimitado número de mensagens/dia

### Capacidade do Sistema:
- Com 1.000 famílias = 1.000 bots
- Cada bot pode enviar 30 msg/s
- Total: 30.000 mensagens/segundo
- **Mais que suficiente para qualquer SaaS!**

---

## 💰 Custos

- **Telegram**: GRATUITO (sempre)
- **Banco de Dados**: ~$10-50/mês (PostgreSQL)
- **Servidor**: ~$20-100/mês (depende do tráfego)

**Total**: ~$30-150/mês para milhares de usuários

---

## 📝 Checklist de Implementação

### Backend
- [ ] Criar tabelas no banco de dados
- [ ] Implementar MultiTenantNotificationService
- [ ] Criar endpoints da API
- [ ] Adicionar middleware de autorização
- [ ] Implementar detecção automática de chat_id
- [ ] Adicionar logs e auditoria

### Frontend
- [ ] Criar tela de setup do Telegram
- [ ] Implementar tutorial interativo
- [ ] Criar interface de gerenciamento de cuidadores
- [ ] Adicionar botão de teste
- [ ] Criar dashboard de status

### Testes
- [ ] Testar criação de bot
- [ ] Testar adição de cuidadores
- [ ] Testar envio de alertas
- [ ] Testar isolamento entre famílias
- [ ] Testar performance com múltiplos bots

---

## 🎯 Próximos Passos

1. Implementar as tabelas no banco
2. Criar os endpoints da API
3. Desenvolver o MultiTenantNotificationService
4. Criar interface de configuração no frontend
5. Testar com múltiplas famílias
6. Documentar para os usuários finais

---

**Arquitetura completa e pronta para implementação!** 🚀
