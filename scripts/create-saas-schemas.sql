-- Script para criar schemas SaaS no banco wifi_movimento existente
-- WiFiSense SaaS Multi-Tenant Platform

-- Conectar ao banco wifi_movimento
\c wifi_movimento

-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Criar schemas isolados para cada microserviço
CREATE SCHEMA IF NOT EXISTS auth_schema;
CREATE SCHEMA IF NOT EXISTS tenant_schema;
CREATE SCHEMA IF NOT EXISTS device_schema;
CREATE SCHEMA IF NOT EXISTS license_schema;
CREATE SCHEMA IF NOT EXISTS event_schema;
CREATE SCHEMA IF NOT EXISTS notification_schema;
CREATE SCHEMA IF NOT EXISTS billing_schema;

-- Comentários descrevendo cada schema
COMMENT ON SCHEMA auth_schema IS 'Schema para autenticação e autorização (auth-service)';
COMMENT ON SCHEMA tenant_schema IS 'Schema para gerenciamento de tenants (tenant-service)';
COMMENT ON SCHEMA device_schema IS 'Schema para gerenciamento de dispositivos (device-service)';
COMMENT ON SCHEMA license_schema IS 'Schema para sistema de licenciamento (license-service)';
COMMENT ON SCHEMA event_schema IS 'Schema para processamento de eventos (event-service)';
COMMENT ON SCHEMA notification_schema IS 'Schema para notificações multi-canal (notification-service)';
COMMENT ON SCHEMA billing_schema IS 'Schema para faturamento e pagamentos (billing-service)';

-- Dar permissões ao usuário postgres
GRANT ALL PRIVILEGES ON SCHEMA auth_schema TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA tenant_schema TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA device_schema TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA license_schema TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA event_schema TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA notification_schema TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA billing_schema TO postgres;

-- Dar permissões em todas as tabelas futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA auth_schema GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA tenant_schema GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA device_schema GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA license_schema GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA event_schema GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA notification_schema GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA billing_schema GRANT ALL ON TABLES TO postgres;

-- Dar permissões em sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA auth_schema GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA tenant_schema GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA device_schema GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA license_schema GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA event_schema GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA notification_schema GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA billing_schema GRANT ALL ON SEQUENCES TO postgres;

-- Mensagem de sucesso
SELECT 'Schemas SaaS criados com sucesso no banco wifi_movimento!' as status;

-- Listar schemas criados
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name LIKE '%_schema'
ORDER BY schema_name;
