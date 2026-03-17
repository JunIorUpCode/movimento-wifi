-- ============================================================================
-- Script SQL para Configuração do Banco de Dados PostgreSQL
-- Sistema: WiFiSense Local
-- ============================================================================

-- Criar banco de dados (execute como superusuário postgres)
-- CREATE DATABASE wifisense;

-- Conectar ao banco de dados
-- \c wifisense

-- ============================================================================
-- TABELA: events
-- Eventos detectados pelo sistema de monitoramento
-- ============================================================================
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    provider VARCHAR(50) DEFAULT 'mock',
    metadata_json TEXT DEFAULT '{}',
    zone_id INTEGER,
    is_false_positive BOOLEAN DEFAULT FALSE,
    user_notes TEXT
);

-- Índices para events
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);

-- ============================================================================
-- TABELA: calibration_profiles
-- Perfis de calibração salvos
-- ============================================================================
CREATE TABLE IF NOT EXISTS calibration_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    baseline_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE NOT NULL
);

-- Índice para calibration_profiles
CREATE INDEX IF NOT EXISTS idx_calibration_profiles_name ON calibration_profiles(name);

-- ============================================================================
-- TABELA: behavior_patterns
-- Padrões de comportamento aprendidos
-- ============================================================================
CREATE TABLE IF NOT EXISTS behavior_patterns (
    id SERIAL PRIMARY KEY,
    hour_of_day INTEGER NOT NULL CHECK (hour_of_day >= 0 AND hour_of_day <= 23),
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    presence_probability FLOAT NOT NULL,
    avg_movement_level FLOAT NOT NULL,
    sample_count INTEGER NOT NULL,
    last_updated TIMESTAMP NOT NULL
);

-- Índice composto para behavior_patterns
CREATE INDEX IF NOT EXISTS idx_hour_day ON behavior_patterns(hour_of_day, day_of_week);

-- ============================================================================
-- TABELA: zones
-- Zonas de monitoramento
-- ============================================================================
CREATE TABLE IF NOT EXISTS zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    rssi_min FLOAT NOT NULL,
    rssi_max FLOAT NOT NULL,
    alert_config_json TEXT DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABELA: performance_metrics
-- Métricas de performance do sistema
-- ============================================================================
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    capture_time_ms FLOAT NOT NULL,
    processing_time_ms FLOAT NOT NULL,
    detection_time_ms FLOAT NOT NULL,
    total_latency_ms FLOAT NOT NULL,
    memory_usage_mb FLOAT NOT NULL,
    cpu_usage_percent FLOAT NOT NULL
);

-- Índice para performance_metrics
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);

-- ============================================================================
-- TABELA: ml_models
-- Metadados de modelos ML treinados
-- ============================================================================
CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    accuracy FLOAT,
    training_samples INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE NOT NULL,
    metadata_json TEXT DEFAULT '{}' NOT NULL
);

-- Índice para ml_models
CREATE INDEX IF NOT EXISTS idx_ml_models_name ON ml_models(name);

-- ============================================================================
-- TABELA: notification_logs
-- Log de notificações enviadas
-- ============================================================================
CREATE TABLE IF NOT EXISTS notification_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    channel VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    recipient VARCHAR(200) NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    alert_data TEXT DEFAULT '{}' NOT NULL
);

-- Índices para notification_logs
CREATE INDEX IF NOT EXISTS idx_notification_logs_timestamp ON notification_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_notification_logs_channel ON notification_logs(channel);

-- ============================================================================
-- VERIFICAÇÃO DAS TABELAS CRIADAS
-- ============================================================================
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================
