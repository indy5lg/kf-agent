"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ApiError,
  PRESET_PROMPTS,
  getCurrentUser,
  requestUploadUrl,
  startRun,
  uploadFile,
  type User,
} from "@/lib/api";
import { stageToCheckpoint } from "@/lib/stageProgress";
import { useRunPolling } from "@/lib/useRunPolling";

export default function ChatPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [project, setProject] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [sentPrompt, setSentPrompt] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          router.push("/login");
        }
      })
      .finally(() => setChecking(false));
  }, [router]);

  const { status, pollingFailed } = useRunPolling(runId);
  const canSend = Boolean(project && file);
  const isTerminal = status?.stage === "succeeded" || status?.stage === "failed";
  const isRunInFlight = runId !== null && !isTerminal && !pollingFailed;
  const username = user ? user.email.split("@")[0] : null;

  async function handleSend(presetPrompt: string) {
    if (!file || isRunInFlight) return;

    setSendError(null);
    setSentPrompt(presetPrompt);
    setRunId(null);

    try {
      const { upload_url } = await requestUploadUrl(project);
      await uploadFile(upload_url, file);
      const { run_id } = await startRun(project, presetPrompt);
      setRunId(run_id);
    } catch (err) {
      setSendError(
        err instanceof ApiError ? err.message : "Could not start the run. Please try again."
      );
    }
  }

  if (checking) {
    return null;
  }

  if (user === null) {
    // Redirect to /login is already in flight; render nothing while it happens.
    return null;
  }

  return (
    <div className="flex flex-1 flex-col bg-zinc-50 dark:bg-black">
      <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-6">
        {sentPrompt && (
          <div className="self-end rounded-lg bg-foreground px-4 py-2 text-background">
            {sentPrompt}
          </div>
        )}

        {sendError && (
          <div className="self-start rounded-lg bg-red-100 px-4 py-2 text-red-700 dark:bg-red-950 dark:text-red-300">
            {sendError}
          </div>
        )}

        {runId && !isTerminal && !pollingFailed && (
          <div className="flex w-full max-w-sm flex-col gap-2 self-start">
            <div
              role="progressbar"
              aria-valuenow={stageToCheckpoint(status?.stage ?? "queued")}
              className="h-2 w-full overflow-hidden rounded-full bg-black/[.08] dark:bg-white/[.145]"
            >
              <div
                className="h-full rounded-full bg-foreground transition-all"
                style={{ width: `${stageToCheckpoint(status?.stage ?? "queued")}%` }}
              />
            </div>
            <span className="text-sm text-zinc-600 dark:text-zinc-400">
              {status?.stage ?? "queued"}
            </span>
          </div>
        )}

        {pollingFailed && (
          <div className="self-start rounded-lg bg-red-100 px-4 py-2 text-red-700 dark:bg-red-950 dark:text-red-300">
            Lost connection to the run.
          </div>
        )}

        {isTerminal && status?.stage === "succeeded" && (
          <div className="self-start rounded-lg bg-white px-4 py-2 dark:bg-zinc-950">
            {JSON.stringify(status.result)}
          </div>
        )}

        {isTerminal && status?.stage === "failed" && (
          <div className="self-start rounded-lg bg-red-100 px-4 py-2 text-red-700 dark:bg-red-950 dark:text-red-300">
            {status.error}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3 border-t border-black/[.08] p-4 dark:border-white/[.145]">
        <p className="text-sm text-zinc-600 dark:text-zinc-400">Signed in as {username}</p>

        <label className="flex flex-col gap-1 text-sm text-zinc-700 dark:text-zinc-300">
          Project
          <input
            type="text"
            value={project}
            onChange={(e) => setProject(e.target.value)}
            className="rounded border border-black/[.08] px-3 py-2 dark:border-white/[.145] dark:bg-black"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm text-zinc-700 dark:text-zinc-300">
          Attach file
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="rounded border border-black/[.08] px-3 py-2 dark:border-white/[.145] dark:bg-black"
          />
        </label>

        <div className="flex flex-wrap gap-2">
          {PRESET_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={!canSend || isRunInFlight}
              onClick={() => handleSend(prompt)}
              className="rounded-full border border-black/[.08] px-4 py-2 text-sm transition-colors hover:bg-black/[.04] disabled:opacity-50 dark:border-white/[.145] dark:hover:bg-[#1a1a1a]"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
