import { useCallback, useEffect, useState } from 'react';
import { fetchDigitalTwinState } from '../lib/api';

/**
 * Loads the digital twin graph state from the backend and exposes a refresh()
 * used after a scenario run to re-colour disrupted nodes.
 */
export default function useDigitalTwin() {
  const [twin, setTwin] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchDigitalTwinState();
      setTwin(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { twin, loading, error, refresh };
}
