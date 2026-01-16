import { useEffect, useState } from "react";
import apiClient from "../services/apiClient";

export function useTrainingStatus(pollInterval = 10000) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchStatus = async () => {
      try {
        const res = await apiClient.get(
          `${import.meta.env.VITE_RASA_TRAINING_BASE_URL}/rasa-training-status`
        );

        if (isMounted) {
          setStatus(res);
          setLoading(false);
        }
      } catch (err) {
        console.error("Failed to fetch training status", err);
        if (isMounted) setLoading(false);
      }
    };

    fetchStatus(); 
    const interval = setInterval(fetchStatus, pollInterval);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [pollInterval]);

  return { status, loading };
}
