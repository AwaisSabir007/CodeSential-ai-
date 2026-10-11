export interface WsEvent {
  type: 'connected' | 'scan_started' | 'scan_completed' | 'finding_detected' | 'file_changed' | 'agent_step' | string;
  project_id?: string;
  data?: Record<string, unknown>;
  message?: string;
  timestamp?: string;
}

class WSClient {
  private url: string;
  private socket: WebSocket | null = null;
  private handlers: Array<(event: WsEvent) => void> = [];
  private reconnectDelay = 1000;
  private maxDelay = 30000;
  private stopped = false;

  constructor(url: string) { this.url = url; }

  connect() {
    if (this.stopped) return;
    this.socket = new WebSocket(this.url);
    this.socket.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data) as WsEvent;
        this.handlers.forEach(h => h(parsed));
      } catch {}
    };
    this.socket.onopen = () => {
      this.reconnectDelay = 1000;
      const connEvent: WsEvent = { type: 'ws_connected' };
      this.handlers.forEach(h => h(connEvent));
    };
    this.socket.onclose = () => {
      const discEvent: WsEvent = { type: 'ws_disconnected' };
      this.handlers.forEach(h => h(discEvent));
      if (!this.stopped) {
        setTimeout(() => {
          this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxDelay);
          this.connect();
        }, this.reconnectDelay);
      }
    };
    this.socket.onerror = () => { this.socket?.close(); };
  }

  onMessage(handler: (event: WsEvent) => void) {
    this.handlers.push(handler);
    if (!this.socket || this.socket.readyState === WebSocket.CLOSED) this.connect();
  }

  disconnect() {
    this.stopped = true;
    this.socket?.close();
  }
}

export const wsClient = new WSClient('ws://127.0.0.1:8765/api/v1/ws/events');
