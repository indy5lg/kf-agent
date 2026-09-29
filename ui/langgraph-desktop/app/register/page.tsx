"use client";

import { useRouter } from "next/navigation";
import { register, ApiError } from "@/lib/api";
import { AuthForm } from "@/components/AuthForm";

export default function RegisterPage() {
  const router = useRouter();

  async function handleRegister(email: string, password: string) {
    try {
      await register(email, password);
      router.push("/login");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        throw new Error("An account with that email already exists.");
      }
      throw new Error("Registration failed. Please try again.");
    }
  }

  return (
    <AuthForm
      title="Create an account"
      submitLabel="Create account"
      loadingLabel="Creating account..."
      onSubmit={handleRegister}
      footer={
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Already have an account?{" "}
          <a href="/login" className="font-medium text-zinc-950 dark:text-zinc-50">
            Log in
          </a>
        </p>
      }
    />
  );
}
