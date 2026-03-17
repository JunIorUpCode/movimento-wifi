-- WiFiSense SaaS Multi-Tenant Platform
-- Script de inicialização dos schemas PostgreSQL
-- Cria schemas isolados para cada microserviço

-- Conectar ao banco wifisense_saas
\c wifisense_saas;

-- Schema para Auth Service (autenticação e autorização)
CREATE SCHEMA IF NOT EXISTS auth_schema;
COMMENT ON SCHEMA auth_schema IS 'Schema para serviço de autenticação - gerencia usuários, tokens JWT e sessões';

-- Schema para Tenant Service (gerenciamento de tenants)
CREATE SCHEMA IF NOT EXISTS tenant_schema;
COMMENT ON SCHEMA tenant_schema IS 'Schema para serviço de tenants - gerencia contas de clientes e configurações';

-- Schema para Device Service (gerenciamento de dispositivos)
CREATE SCHEMA IF NOT EXISTS device_schema;
COMMENT ON SCHEMA device_schema IS 'Schema para serviço de dispositivos - gerencia registro e status de dispositivos';

-- Schema para License Service (licenciamento)
CREATE SCHEMA IF NOT EXISTS license_schema;
COMMENT ON SCHEMA license_schema IS 'Schema para serviço de licenças - gerencia chaves de ativação e validação';

-- Schema para Event Service (processamento de eventos)
CREATE SCHEMA IF NOT EXISTS event_schema;
COMMENT ON SCHEMA event_schema IS 'Schema para serviço de eventos - armazena eventos detectados e histórico';

-- Schema para Notification Service (notificações)
CREATE SCHEMA IF NOT EXISTS notification_schema;
COMMENT ON SCHEMA notification_schema IS 'Schema para serviço de notificações - gerencia configurações e logs de notificações';

-- Schema para Billing Service (faturamento)
CREATE SCHEMA IF NOT EXISTS billing_schema;
COMMENT ON SCHEMA billing_schema IS 'Schema para serviço de faturamento - gerencia faturas, pagamentos e Stripe';

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
COMMENT ON EXTENSION "uuid-ossp" IS 'Geração de UUIDs para IDs únicos';

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
COMMENT ON EXTENSION "pgcrypto" IS 'Funções criptográficas para hashing e encriptação';

-- Garantir permissões para o usuário wifisense em todos os schemas
GRANT ALL PRIVILEGES ON SCHEMA auth_schema TO wifisense;
GRANT ALL PRIVILEGES ON SCHEMA tenant_schema TO wifisense;
GRANT ALL PRIVILEGES ON SCHEMA device_schema TO wifisense;
GRANT ALL PRIVILEGES ON SCHEMA license_schema TO wifisense;
GRANT ALL PRIVILEGES ON SCHEMA event_schema TO wifisense;
GRANT ALL PRIVILEGES ON SCHEMA notification_schema TO wifisense;
GRANT ALL PRIVILEGES ON SCHEMA billing_schema TO wifisense;

-- Garantir permissões em todas as tabelas futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA auth_schema GRANT ALL ON TABLES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA tenant_schema GRANT ALL ON TABLES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA device_schema GRANT ALL ON TABLES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA license_schema GRANT ALL ON TABLES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA event_schema GRANT ALL ON TABLES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA notification_schema GRANT ALL ON TABLES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA billing_schema GRANT ALL ON TABLES TO wifisense;

-- Garantir permissões em sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA auth_schema GRANT ALL ON SEQUENCES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA tenant_schema GRANT ALL ON SEQUENCES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA device_schema GRANT ALL ON SEQUENCES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA license_schema GRANT ALL ON SEQUENCES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA event_schema GRANT ALL ON SEQUENCES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA notification_schema GRANT ALL ON SEQUENCES TO wifisense;
ALTER DEFAULT PRIVILEGES IN SCHEMA billing_schema GRANT ALL ON SEQUENCES TO wifisense;

-- Log de inicialização
DO $$
BEGIN
    RAISE NOTICE 'Schemas criados com sucesso:';
    RAISE NOTICE '  - auth_schema';
    RAISE NOTICE '  - tenant_schema';
    RAISE NOTICE '  - device_schema';
    RAISE NOTICE '  - license_schema';
    RAISE NOTICE '  - event_schema';
    RAISE NOTICE '  - notification_schema';
    RAISE NOTICE '  - billing_schema';
    RAISE NOTICE 'Extensões habilitadas: uuid-ossp, pgcrypto';
    RAISE NOTICE 'Permissões concedidas ao usuário wifisense';
END $$;
