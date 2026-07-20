import { useCallback, useEffect, useRef, useState } from 'react';
import { streamUrl } from '../lib/api';

/**
 * Opens an SSE connection to /api/scenario/stream/{sessionId}.
 * Exposes: messages[], isStreaming, isHITLRequired, finalRecommendation.
 * Reconnects automatically if the connection drops mid-run.
 */
export default function useAgentStream(sessionId) {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isHITLRequired, setIsHITLRequired] = useState(false);
  const [finalRecommendation, setFinalRecommendation] = useState(null);
  const sourceRef = useRef(null);
  const completedRef = useRef(false);

  const disconnect = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const connect = useCallback(() => {
    if (!sessionId) return;
    completedRef.current = false;
    setMessages([]);
    setIsHITLRequired(false);
    setFinalRecommendation(null);
    setIsStreaming(true);

    const source = new EventSource(streamUrl(sessionId));
    sourceRef.current = source;

    source.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch {
        return;
      }
      if (payload.type === 'hitl_required') {
        setIsHITLRequired(true);
        setFinalRecommendation(payload.recommendation);
      } else if (payload.type === 'complete') {
        completedRef.current = true;
        setIsHITLRequired(false);
        disconnect();
      } else if (payload.type === 'error') {
        setMessages((prev) => [
          ...prev,
          { agent: 'system', message: `Error: ${payload.message}`, timestamp: new Date().toISOString() },
        ]);
      } else if (payload.agent) {
        setMessages((prev) => [...prev, payload]);
      }
    };

    source.onerror = () => {
      source.close();
      sourceRef.current = null;
      if (!completedRef.current) {
        setTimeout(() => {
          if (!completedRef.current && sessionId) {
            const retry = new EventSource(streamUrl(sessionId));
            sourceRef.current = retry;
            retry.onmessage = source.onmessage;
            retry.onerror = source.onerror;
          }
        }, 2000);
      } else {
        setIsStreaming(false);
      }
    };
  }, [sessionId, disconnect]);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  const clearHITL = useCallback(() => setIsHITLRequired(false), []);

  /** Drop the previous run's output immediately, before the next request's
   *  data starts arriving, so old content never lingers on screen. */
  const resetRun = useCallback(() => {
    completedRef.current = true; // suppress the reconnect path while tearing down
    disconnect();
    setMessages([]);
    setIsHITLRequired(false);
    setFinalRecommendation(null);
  }, [disconnect]);

  return {
    messages,
    isStreaming,
    isHITLRequired,
    finalRecommendation,
    clearHITL,
    resetRun,
  };
}
