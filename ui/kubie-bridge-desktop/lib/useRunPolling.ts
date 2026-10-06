"use client";

import { useEffect, useState } from "react";
import { getRunStatus, type RunStatus } from "./api";

const POLL_INTERVAL_MS = 2000;
const MAX_CONSECUTIVE_FAILURES = 5;

type RunPollingState = {
  status: RunStatus | null;
  pollingFailed: boolean;
};

export function useRunPolling(runId: string | null): RunPollingState {
  const [status, setStatus] = useState<RunStatus | null>(null);
  const [pollingFailed, setPollingFailed] = useState(false);

  useEffect(() => {
    if (!runId) {
      return;
    }

    let cancelled = false;
    let failureCount = 0;

    const intervalId = setInterval(async () => {
      try {
        const next = await getRunStatus(runId);
        if (cancelled) return;
        failureCount = 0;
        setStatus(next);
        if (next.stage === "succeeded" || next.stage === "failed") {
          clearInterval(intervalId);
        }
      } catch {
        if (cancelled) return;
        failureCount += 1;
        if (failureCount >= MAX_CONSECUTIVE_FAILURES) {
          clearInterval(intervalId);
          setPollingFailed(true);
        }
      }
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [runId]);

  return { status, pollingFailed };
}
