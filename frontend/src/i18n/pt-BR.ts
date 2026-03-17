// Traduções PT-BR — WiFiSense Local
export const ptBR = {
  // Navegação
  nav: {
    dashboard:        "Painel",
    history:          "Histórico",
    calibration:      "Calibração",
    statistics:       "Estatísticas",
    notifications:    "Notificações",
    zones:            "Zonas",
    ml:               "Dados ML",
    pushNotifications:"Notif. Push",
    replay:           "Replay",
    settings:         "Configurações",
  },

  // Status de presença
  presence: {
    PRESENCE_MOVING:       "Movimento Detectado",
    PRESENCE_STILL:        "Presença Estática",
    NO_PRESENCE:           "Sem Presença",
    FALL_SUSPECTED:        "Queda Suspeita",
    PROLONGED_INACTIVITY:  "Inatividade Prolongada",
    UNKNOWN:               "Desconhecido",
  },

  // Dashboard
  dashboard: {
    title:            "Painel Principal",
    signal:           "Sinal",
    confidence:       "Confiança",
    status:           "Status",
    lastEvent:        "Último Evento",
    monitorActive:    "Monitor Ativo",
    monitorStopped:   "Monitor Parado",
    startMonitor:     "Iniciar Monitor",
    stopMonitor:      "Parar Monitor",
    noEvents:         "Nenhum evento registrado.",
  },

  // Calibração
  calibration: {
    title:            "Calibração",
    start:            "Iniciar Calibração",
    stop:             "Parar",
    progress:         "Progresso",
    baseline:         "Linha de Base",
    profiles:         "Perfis",
    saveProfile:      "Salvar Perfil",
    loadProfile:      "Carregar Perfil",
    deleteProfile:    "Excluir Perfil",
    instructions:     "Mantenha o ambiente vazio durante a calibração.",
    movementDetected: "Movimento detectado! Aguarde e tente novamente.",
    success:          "Calibração concluída com sucesso.",
  },

  // Alertas
  alerts: {
    fallDetected:     "⚠️ Queda detectada!",
    inactivity:       "Inatividade prolongada detectada.",
    connectionLost:   "Conexão com o servidor perdida.",
    connectionOk:     "Conectado ao servidor.",
  },

  // Geral
  common: {
    save:     "Salvar",
    cancel:   "Cancelar",
    delete:   "Excluir",
    edit:     "Editar",
    confirm:  "Confirmar",
    loading:  "Carregando...",
    error:    "Erro",
    success:  "Sucesso",
    back:     "Voltar",
    close:    "Fechar",
    yes:      "Sim",
    no:       "Não",
  },
} as const;

export type I18nKeys = typeof ptBR;
