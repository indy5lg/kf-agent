"use client";

import { useRouter } from "next/navigation";
import { login, ApiError } from "@/lib/api";
import { AuthForm } from "@/components/AuthForm";

export default function LoginPage() {
  const router = useRouter();

  async function handleLogin(email: string, password: string) {
    try {
      await login(email, password);
      router.push("/");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        throw new Error("Invalid email or password.");
      }
      throw new Error("Login failed. Please try again.");
    }
  }

  return (
    <AuthForm
      title="Log in"
      submitLabel="Log in"
      loadingLabel="Logging in..."
      onSubmit={handleLogin}
      footer={
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Need an account?{" "}
          <a href="/register" className="font-medium text-zinc-950 dark:text-zinc-50">
            Register
          </a>
        </p>
      }
    />
  );
}
