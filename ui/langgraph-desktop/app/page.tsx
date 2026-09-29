"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser, logout, ApiError, User } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          router.push("/login");
          return;
        }
        setError(
          "Something went wrong loading your account. Please try refreshing the page."
        );
      })
      .finally(() => setChecking(false));
  }, [router]);

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  if (checking) {
    return null;
  }

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center bg-zinc-50 dark:bg-black">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (user === null) {
    // Redirect to /login is already in flight; render nothing while it happens.
    return null;
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 bg-zinc-50 dark:bg-black">
      <p className="text-lg text-black dark:text-zinc-50">
        Welcome, {user.email}
      </p>
      <button
        onClick={handleLogout}
        className="rounded-full border border-black/[.08] px-5 py-2 text-black transition-colors hover:bg-black/[.04] dark:border-white/[.145] dark:text-zinc-50 dark:hover:bg-[#1a1a1a]"
      >
        Log out
      </button>
    </div>
  );
}
