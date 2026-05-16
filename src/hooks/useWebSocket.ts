import { useCallback, useEffect, useRef, useState } from 'react';
import { WsPayload } from '../types';

interface UseWebSocketOptions {
  onMessage: (payload: WsPayload) => void;
  reconnectDelayMs?: number;
}

export function useWebSocket(url: string, options: UseWebSocketOptions) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);
  // Keep a stable ref to the callback so the connect closure never goes stale
  const onMessageRef = useRef(options.onMessage);
  onMessageRef.current = options.onMessage;

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (mountedRef.current) setConnected(true);
    };

    ws.onmessage = (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data as string) as WsPayload;
        onMessageRef.current(payload);
      } catch {
        // malformed frame — ignore
      }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setConnected(false);
      timerRef.current = setTimeout(connect, options.reconnectDelayMs ?? 3000);
    };

    ws.onerror = () => ws.close();
  }, [url, options.reconnectDelayMs]);

  // Keep-alive ping every 25 s so the server timeout doesn't fire
  useEffect(() => {
    if (!connected) return;
    const id = setInterval(() => {
      wsRef.current?.send(JSON.stringify({ type: 'ping' }));
    }, 25_000);
    return () => clearInterval(id);
  }, [connected]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected };
}
