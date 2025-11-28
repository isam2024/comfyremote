/**
 * React hook for Server-Sent Events (SSE)
 * Manages SSE connection with auto-reconnect
 */
import { useEffect, useRef, useState } from 'react';

const SSE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/stream/events`
  : '/api/stream/events';

export function useSSE(onMessage) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const onMessageRef = useRef(onMessage);

  // Keep the callback ref updated
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    function connect() {
      try {
        console.log('Connecting to SSE...');

        const eventSource = new EventSource(SSE_URL);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          console.log('SSE connected');
          setConnected(true);
          setError(null);
          reconnectAttempts.current = 0;
        };

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            // Handle different event types
            if (data.type === 'connected') {
              console.log('SSE connection confirmed:', data);
            } else if (onMessageRef.current) {
              onMessageRef.current(data);
            }
          } catch (err) {
            console.error('Error parsing SSE message:', err);
          }
        };

        eventSource.onerror = (err) => {
          console.error('SSE error:', err);
          setConnected(false);
          setError(err);

          // Close current connection
          eventSource.close();

          // Attempt reconnect with exponential backoff
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectAttempts.current += 1;

          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        };

      } catch (err) {
        console.error('Error creating EventSource:', err);
        setError(err);
      }
    }

    // Initial connection
    connect();

    // Cleanup on unmount
    return () => {
      console.log('Cleaning up SSE connection');

      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, []); // Empty dependency array - connection persists for component lifetime

  return { connected, error };
}

export default useSSE;
