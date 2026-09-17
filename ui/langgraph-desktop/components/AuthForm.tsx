"use client";

import { useState } from "react";
import type { ReactNode } from "react";

type AuthFormProps = {
  title: string;
  submitLabel: string;
  loadingLabel: string;
  onSubmit: (email: string, password: string) => Promise<void>;
  footer: ReactNode;
};

export function AuthForm({
  title,
  submitLabel,
  loadingLabel,
  onSubmit,
  footer,
}: AuthFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await onSubmit(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center bg-zinc-50 dark:bg-black">
      <form
        onSubmit={handleSubmit}
        className="flex w-full max-w-sm flex-col gap-4 rounded-lg border border-black/[.08] bg-white p-8 dark:border-white/[.145] dark:bg-zinc-950"
      >
        <div className="flex items-center gap-2">
          <span
            data-testid="kubie-mark"
            className="flex h-8 w-8 items-center justify-center rounded-full bg-foreground text-sm font-bold text-background"
            aria-hidden="true"
          >
            K
          </span>
          <span className="text-lg font-semibold text-black dark:text-zinc-50">
            Kubie
          </span>
        </div>
        <h1 className="text-xl font-semibold text-black dark:text-zinc-50">
          {title}
        </h1>
        <label className="flex flex-col gap-1 text-sm text-zinc-700 dark:text-zinc-300">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded border border-black/[.08] px-3 py-2 dark:border-white/[.145] dark:bg-black"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-zinc-700 dark:text-zinc-300">
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded border border-black/[.08] px-3 py-2 dark:border-white/[.145] dark:bg-black"
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="rounded-full bg-foreground px-5 py-2 text-background transition-colors hover:bg-[#383838] disabled:opacity-50 dark:hover:bg-[#ccc]"
        >
          {loading ? loadingLabel : submitLabel}
        </button>
        {footer}
      </form>
    </div>
  );
}
