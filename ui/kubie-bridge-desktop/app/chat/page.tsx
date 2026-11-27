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
import { stageToCheckpoint } from "@/lib/stageProgress";
import { useRunPolling } from "@/lib/useRunPolling";
import { FileDropZone } from "@/components/FileDropZone";
import { ProcessingCube } from "@/components/ProcessingCube";
import { RunOutcome, isTerminalStatus } from "@/components/RunOutcome";
import { UploadHeader } from "@/components/UploadHeader";

export default function ChatPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [project, setProject] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [sentPrompt, setSentPrompt] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);
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
  const isTerminal = status !== null && isTerminalStatus(status);
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

  async function handleLogout() {
    setLogoutError(null);
    try {
      await logout();
    } catch {
      setLogoutError("Could not log out. Please try again.");
      return;
    }
    router.push("/login");
  }

  if (checking) {
    return null;
  }

  if (user === null || username === null) {
    // Redirect to /login is already in flight; render nothing while it happens.
    return null;
  }

  const stage = status?.stage ?? "queued";

  return (
    <div className="flex flex-1 flex-col bg-zinc-50 dark:bg-black">
      <UploadHeader username={username} onLogout={handleLogout} />

      {logoutError && (
        <p
          role="alert"
          className="bg-red-100 px-6 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300"
        >
          {logoutError}
        </p>
      )}

      <main className="flex flex-1 items-start justify-center px-4 py-10">
        <div className="flex w-full max-w-2xl flex-col gap-6 rounded-2xl border border-black/[.08] bg-white p-6 sm:p-8 dark:border-white/[.145] dark:bg-zinc-950">
          <div>
            <h1 className="text-2xl font-semibold text-black dark:text-zinc-50">
              Run a pipeline script
            </h1>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Name a project, attach your training script, then pick what you want done with it.
            </p>
          </div>

          {!sentPrompt && (
            <section
              aria-labelledby="instructions-heading"
              className="rounded-xl bg-zinc-50 p-5 text-sm text-zinc-700 dark:bg-black dark:text-zinc-300"
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

          {(sentPrompt || sendError || runId) && (
            <section className="flex flex-col items-center gap-4 rounded-xl bg-zinc-50 p-4 dark:bg-black">
              {sentPrompt && (
                <div className="self-end rounded-lg bg-foreground px-4 py-2 text-sm text-background">
                  {sentPrompt}
                </div>
              )}

              {sendError && (
                <div className="w-full rounded-lg bg-red-100 px-4 py-2 text-red-700 dark:bg-red-950 dark:text-red-300">
                  {sendError}
                </div>
              )}

              {isRunInFlight && (
                <div className="flex w-full max-w-sm flex-col items-center gap-2">
                  <ProcessingCube />
                  <div
                    role="progressbar"
                    aria-valuenow={stageToCheckpoint(stage)}
                    className="h-2 w-full overflow-hidden rounded-full bg-black/[.08] dark:bg-white/[.145]"
                  >
                    <div
                      className="h-full rounded-full bg-foreground transition-all"
                      style={{ width: `${stageToCheckpoint(stage)}%` }}
                    />
                  </div>
                  <span className="text-sm text-zinc-600 dark:text-zinc-400">{stage}</span>
                </div>
              )}

              {pollingFailed && (
                <div className="w-full rounded-lg bg-red-100 px-4 py-2 text-red-700 dark:bg-red-950 dark:text-red-300">
                  Lost connection to the run.
                </div>
              )}

              {status !== null && isTerminalStatus(status) && <RunOutcome status={status} />}
            </section>
          )}

          <div className="flex flex-col gap-4">
            <label className="flex flex-col gap-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Project
              <input
                type="text"
                value={project}
                onChange={(e) => setProject(e.target.value)}
                placeholder="e.g. mnist-classifier"
                className="rounded-lg border border-black/[.08] px-3 py-2 font-normal dark:border-white/[.145] dark:bg-black"
              />
            </label>

            <FileDropZone file={file} onFileChange={setFile} disabled={isRunInFlight} />

            <div className="grid gap-2 sm:grid-cols-3">
              {PRESET_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  disabled={!canSend || isRunInFlight}
                  onClick={() => handleSend(prompt)}
                  className="rounded-xl border border-black/[.08] px-4 py-3 text-sm font-medium text-black transition-colors hover:border-foreground hover:bg-black/[.04] disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-black/[.08] disabled:hover:bg-transparent dark:border-white/[.145] dark:text-zinc-50 dark:hover:bg-white/[.06]"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
