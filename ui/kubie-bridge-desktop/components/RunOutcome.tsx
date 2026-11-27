import type { RunStatus } from "@/lib/api";

type TerminalRunStatus = RunStatus & { stage: "succeeded" | "failed" };

type RunOutcomeProps = {
  status: TerminalRunStatus;
};

export function RunOutcome({ status }: RunOutcomeProps) {
  if (status.stage === "failed") {
    return (
      <div className="w-full rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950">
        <h3 className="font-semibold text-red-800 dark:text-red-200">Run failed</h3>
        <p className="mt-1 text-sm text-red-700 dark:text-red-300">{status.error}</p>
      </div>
    );
  }

  return (
    <div className="w-full rounded-xl border border-black/[.08] bg-white p-4 dark:border-white/[.145] dark:bg-zinc-950">
      <h3 className="font-semibold text-black dark:text-zinc-50">Run succeeded</h3>
      {typeof status.result === "string" ? (
        <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">{status.result}</p>
      ) : (
        <pre className="mt-2 overflow-x-auto rounded-lg bg-zinc-100 p-3 font-mono text-xs text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200">
          {JSON.stringify(status.result, null, 2)}
        </pre>
      )}
    </div>
  );
}

export function isTerminalStatus(status: RunStatus): status is TerminalRunStatus {
  return status.stage === "succeeded" || status.stage === "failed";
}
