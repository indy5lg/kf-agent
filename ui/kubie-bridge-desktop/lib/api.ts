const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export type User = {
  id: string;
  email: string;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: options.credentials ?? "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function register(email: string, password: string): Promise<User> {
  return request<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function login(email: string, password: string): Promise<User> {
  return request<User>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function logout(): Promise<void> {
  return request<void>("/auth/logout", { method: "POST" });
}

export function getCurrentUser(): Promise<User> {
  return request<User>("/auth/me");
}

export type Stage =
  | "queued"
  | "validating"
  | "running"
  | "finalizing"
  | "succeeded"
  | "failed";

export type RunStatus = {
  stage: Stage;
  result: unknown;
  error: string | null;
};

export const PRESET_PROMPTS = [
  "Explain this pipeline",
  "Suggest hyperparameter changes",
  "Convert to a Kubeflow pipeline",
] as const;

export function requestUploadUrl(project: string): Promise<{ upload_url: string }> {
  return request<{ upload_url: string }>("/uploads", {
    method: "POST",
    body: JSON.stringify({ project }),
  });
}

export async function uploadFile(uploadUrl: string, file: File): Promise<void> {
  const response = await fetch(uploadUrl, { method: "PUT", body: file });
  if (!response.ok) {
    throw new ApiError(response.status, `Upload failed: ${response.statusText}`);
  }
}

export function startRun(
  project: string,
  presetPrompt: string
): Promise<{ run_id: string }> {
  return request<{ run_id: string }>("/runs", {
    method: "POST",
    body: JSON.stringify({ project, preset_prompt: presetPrompt }),
  });
}

export function getRunStatus(runId: string): Promise<RunStatus> {
  return request<RunStatus>(`/runs/${runId}/status`);
}
