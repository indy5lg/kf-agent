"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ApiError,
  PRESET_PROMPTS,
  getCurrentUser,
  logout,
  requestUploadUrl,
  startRun,
  uploadFile,
  type User,
} from "@/lib/api";
import { FileDropZone } from "@/components/FileDropZone";
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
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);

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

  async function handleLogout() {
    setLoggingOut(true);
    setLogoutError(null);
    try {
      await logout();
    } catch (err) {
      setLoggingOut(false);
      setLogoutError(
        `Could not log out: ${err instanceof ApiError ? err.message : String(err)}`
      );
      return;
    }
    router.push("/login");
  }

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
      <header className="flex items-center justify-between gap-4 border-b border-black/[.08] px-6 py-3 dark:border-white/[.145]">
        <div className="flex items-center gap-2">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-full bg-foreground text-sm font-bold text-background"
            aria-hidden="true"
          >
            K
          </span>
          <span className="text-lg font-semibold text-black dark:text-zinc-50">Kubie-Bridge</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-zinc-600 dark:text-zinc-400">Signed in as {username}</span>
          <button
            type="button"
            onClick={handleLogout}
            disabled={loggingOut}
            className="rounded-full border border-black/[.08] px-4 py-1.5 text-sm font-medium transition-colors hover:bg-black/[.04] disabled:opacity-50 dark:border-white/[.145] dark:hover:bg-[#1a1a1a]"
          >
            Log out
          </button>
        </div>
      </header>

      <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-6">
        {logoutError && (
          <div className="self-start rounded-lg bg-red-100 px-4 py-2 text-red-700 dark:bg-red-950 dark:text-red-300">
            {logoutError}
          </div>
        )}

        {!sentPrompt && (
          <section
            aria-labelledby="instructions-heading"
            className="max-w-2xl rounded-lg border border-black/[.08] bg-white p-5 text-sm text-zinc-700 dark:border-white/[.145] dark:bg-zinc-950 dark:text-zinc-300"
          >
            <h2
              id="instructions-heading"
              className="mb-3 text-base font-semibold text-black dark:text-zinc-50"
            >
              How to run your ML script on Kubeflow
            </h2>
            <ol className="flex list-decimal flex-col gap-2 pl-5">
              <li>
                <strong>Prepare</strong> a single Python (<code>.py</code>) training script that
                runs on its own. You don&apos;t need to write any Kubeflow or Kubernetes code.
              </li>
              <li>
                <strong>Name your project</strong> with letters, numbers, dashes or underscores.
                Re-using a name replaces that project&apos;s script.
              </li>
              <li>
                <strong>Upload</strong> the script by dragging it into the box below or choosing
                it with Browse files.
              </li>
              <li>
                <strong>Submit</strong> by choosing an action. Progress appears here while the
                agent prepares and runs your pipeline.
              </li>
            </ol>
          </section>
        )}

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
        <label className="flex flex-col gap-1 text-sm text-zinc-700 dark:text-zinc-300">
          Project
          <input
            type="text"
            value={project}
            onChange={(e) => setProject(e.target.value)}
            className="rounded border border-black/[.08] px-3 py-2 dark:border-white/[.145] dark:bg-black"
          />
        </label>

        <FileDropZone file={file} onFileChange={setFile} disabled={isRunInFlight} />

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
