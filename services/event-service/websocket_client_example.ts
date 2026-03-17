/**
 * WebSocket Client Example - Cliente WebSocket com Reconexão Automática
 * Task 17.4: Implementar reconexão automática no frontend
 * Requisitos: 38.5-38.8
 * 
 * Este arquivo demonstra como implementar um cliente WebSocket robusto
 * com reconexão automática, heartbeat e tratamento de erros.
 */

/**
 * Configuração do WebSocket
 */
interface WebSocketConfig {
  /** URL do WebSocket (wss://api.wifisense.com/ws) */
  url: string;
  /** JWT token para autenticação */
  token: string;
  /** Intervalo de heartbeat em milissegundos (padrão: 30000 = 30s) */
  heartbeatInterval?: number;
  /** Timeout de reconexão em milissegundos (padrão: 5000 = 5s) */
  reconnectTimeout?: number;
  /** Máximo de tentativas de reconexão (padrão: Infinity) */
  maxReconnectAttempts?: number;
  /** Callback quando conectado */
  onConnected?: () => void;
  /** Callback quando desconectado */
  onDisconnected?: () => void;
  /** Callback quando recebe evento */
  onEvent?: (event: EventData) => void;
  /** Callback quando ocorre erro */
  onError?: (error: Error) => void;
}

/**
 * Dados de um evento recebido via WebSocket
 */
interface EventData {
  event_id: string;
  device_id: string;
  event_type: 'presence' | 'movement' | 'fall_suspected' | 'prolonged_inactivity';
  confidence: number;
  timestamp: string;
  metadata: Record<string, any>;
}

/**
 * Mensagem recebida do WebSocket
 */
interface WebSocketMessage {
  type: 'connected' | 'event' | 'pong';
  message?: string;
  tenant_id?: string;
  channel?: string;
  timestamp?: string;
  heartbeat_interval?: number;
  idle_timeout?: number;
  data?: EventData;
}

/**
 * Cliente WebSocket com Reconexão Automática
 * 
 * **Funcionalidades**:
 * - Autenticação via JWT token
 * - Heartbeat automático a cada 30 segundos
 * - Reconexão automática com exponential backoff
 * - Tratamento de erros e timeouts
 * - Callbacks para eventos
 * 
 * **Uso**:
 * ```typescript
 * const client = new WebSocketClient({
 *   url: 'wss://api.wifisense.com/ws',
 *   token: localStorage.getItem('jwt_token'),
 *   onEvent: (event) => {
 *     console.log('Novo evento:', event);
 *     // Atualizar UI com o evento
 *   },
 *   onConnected: () => {
 *     console.log('WebSocket conectado');
 *   },
 *   onDisconnected: () => {
 *     console.log('WebSocket desconectado');
 *   }
 * });
 * 
 * client.connect();
 * 
 * // Quando não precisar mais:
 * client.disconnect();
 * ```
 */
export class WebSocketClient {
  private config: Required<WebSocketConfig>;
  private ws: WebSocket | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private isManualDisconnect = false;
  private isConnected = false;

  constructor(config: WebSocketConfig) {
    // Configuração padrão
    this.config = {
      url: config.url,
      token: config.token,
      heartbeatInterval: config.heartbeatInterval || 30000, // 30 segundos
      reconnectTimeout: config.reconnectTimeout || 5000, // 5 segundos
      maxReconnectAttempts: config.maxReconnectAttempts || Infinity,
      onConnected: config.onConnected || (() => {}),
      onDisconnected: config.onDisconnected || (() => {}),
      onEvent: config.onEvent || (() => {}),
      onError: config.onError || ((error) => console.error('WebSocket error:', error))
    };
  }

  /**
   * Conecta ao WebSocket
   */
  public connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.warn('WebSocket já está conectado');
      return;
    }

    this.isManualDisconnect = false;

    try {
      // Constrói URL com token como query parameter
      const wsUrl = `${this.config.url}?token=${this.config.token}`;
      
      console.log('Conectando ao WebSocket...');
      this.ws = new WebSocket(wsUrl);

      // Event listeners
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);

    } catch (error) {
      console.error('Erro ao conectar WebSocket:', error);
      this.config.onError(error as Error);
      this.scheduleReconnect();
    }
  }

  /**
   * Desconecta do WebSocket
   */
  public disconnect(): void {
    console.log('Desconectando WebSocket...');
    
    this.isManualDisconnect = true;
    this.stopHeartbeat();
    this.cancelReconnect();

    if (this.ws) {
      this.ws.close(1000, 'Desconexão manual');
      this.ws = null;
    }

    this.isConnected = false;
  }

  /**
   * Verifica se está conectado
   */
  public get connected(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Handler: WebSocket aberto
   */
  private handleOpen(event: Event): void {
    console.log('WebSocket conectado');
    
    this.isConnected = true;
    this.reconnectAttempts = 0;
    
    // Inicia heartbeat
    this.startHeartbeat();
  }

  /**
   * Handler: Mensagem recebida
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'connected':
          // Mensagem de boas-vindas
          console.log('WebSocket autenticado:', {
            tenant_id: message.tenant_id,
            channel: message.channel,
            heartbeat_interval: message.heartbeat_interval,
            idle_timeout: message.idle_timeout
          });
          
          // Atualiza intervalo de heartbeat se fornecido
          if (message.heartbeat_interval) {
            this.config.heartbeatInterval = message.heartbeat_interval * 1000;
            this.startHeartbeat(); // Reinicia com novo intervalo
          }
          
          this.config.onConnected();
          break;

        case 'event':
          // Evento detectado
          if (message.data) {
            console.log('Evento recebido:', message.data);
            this.config.onEvent(message.data);
          }
          break;

        case 'pong':
          // Resposta ao heartbeat
          console.debug('Heartbeat pong recebido:', message.timestamp);
          break;

        default:
          console.warn('Tipo de mensagem desconhecido:', message.type);
      }

    } catch (error) {
      console.error('Erro ao processar mensagem:', error);
      this.config.onError(error as Error);
    }
  }

  /**
   * Handler: Erro no WebSocket
   */
  private handleError(event: Event): void {
    console.error('Erro no WebSocket:', event);
    
    const error = new Error('WebSocket error');
    this.config.onError(error);
  }

  /**
   * Handler: WebSocket fechado
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket fechado:', {
      code: event.code,
      reason: event.reason,
      wasClean: event.wasClean
    });

    this.isConnected = false;
    this.stopHeartbeat();
    this.config.onDisconnected();

    // Reconecta automaticamente se não foi desconexão manual
    if (!this.isManualDisconnect) {
      this.scheduleReconnect();
    }
  }

  /**
   * Inicia heartbeat (ping a cada 30 segundos)
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        console.debug('Enviando heartbeat ping');
        this.ws.send('ping');
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Para heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Agenda reconexão com exponential backoff
   * 
   * **Exponential Backoff**:
   * - Tentativa 1: 1 segundo
   * - Tentativa 2: 2 segundos
   * - Tentativa 3: 4 segundos
   * - Tentativa 4: 8 segundos
   * - Tentativa 5: 16 segundos
   * - Tentativa 6+: 30 segundos (máximo)
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('Máximo de tentativas de reconexão atingido');
      this.config.onError(new Error('Máximo de tentativas de reconexão atingido'));
      return;
    }

    this.cancelReconnect();

    // Exponential backoff: 2^n segundos, máximo 30 segundos
    const delay = Math.min(
      Math.pow(2, this.reconnectAttempts) * 1000,
      30000
    );

    this.reconnectAttempts++;

    console.log(`Reconectando em ${delay / 1000}s (tentativa ${this.reconnectAttempts})...`);

    this.reconnectTimer = setTimeout(() => {
      console.log('Tentando reconectar...');
      this.connect();
    }, delay);
  }

  /**
   * Cancela reconexão agendada
   */
  private cancelReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

/**
 * Hook React para usar WebSocket
 * 
 * **Uso**:
 * ```typescript
 * function DashboardPage() {
 *   const [events, setEvents] = useState<EventData[]>([]);
 *   const [isConnected, setIsConnected] = useState(false);
 * 
 *   const { connect, disconnect } = useWebSocket({
 *     url: 'wss://api.wifisense.com/ws',
 *     token: localStorage.getItem('jwt_token'),
 *     onEvent: (event) => {
 *       setEvents(prev => [event, ...prev]);
 *       // Mostrar notificação
 *       toast.success(`Novo evento: ${event.event_type}`);
 *     },
 *     onConnected: () => setIsConnected(true),
 *     onDisconnected: () => setIsConnected(false)
 *   });
 * 
 *   useEffect(() => {
 *     connect();
 *     return () => disconnect();
 *   }, []);
 * 
 *   return (
 *     <div>
 *       <div>Status: {isConnected ? 'Conectado' : 'Desconectado'}</div>
 *       <EventList events={events} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useWebSocket(config: WebSocketConfig) {
  const clientRef = React.useRef<WebSocketClient | null>(null);

  const connect = React.useCallback(() => {
    if (!clientRef.current) {
      clientRef.current = new WebSocketClient(config);
    }
    clientRef.current.connect();
  }, [config]);

  const disconnect = React.useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }
  }, []);

  const isConnected = React.useMemo(() => {
    return clientRef.current?.connected || false;
  }, [clientRef.current]);

  return { connect, disconnect, isConnected };
}

/**
 * Exemplo de uso em Vue.js
 * 
 * ```typescript
 * import { ref, onMounted, onUnmounted } from 'vue';
 * import { WebSocketClient } from './websocket_client';
 * 
 * export default {
 *   setup() {
 *     const events = ref<EventData[]>([]);
 *     const isConnected = ref(false);
 *     let wsClient: WebSocketClient | null = null;
 * 
 *     onMounted(() => {
 *       wsClient = new WebSocketClient({
 *         url: 'wss://api.wifisense.com/ws',
 *         token: localStorage.getItem('jwt_token'),
 *         onEvent: (event) => {
 *           events.value.unshift(event);
 *         },
 *         onConnected: () => {
 *           isConnected.value = true;
 *         },
 *         onDisconnected: () => {
 *           isConnected.value = false;
 *         }
 *       });
 * 
 *       wsClient.connect();
 *     });
 * 
 *     onUnmounted(() => {
 *       wsClient?.disconnect();
 *     });
 * 
 *     return { events, isConnected };
 *   }
 * };
 * ```
 */
