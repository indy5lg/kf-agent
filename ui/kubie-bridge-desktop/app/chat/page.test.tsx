import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatPage from "./page";
import * as api from "@/lib/api";

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
  PRESET_PROMPTS: [
    "Explain this pipeline",
    "Suggest hyperparameter changes",
    "Convert to a Kubeflow pipeline",
  ],
  getCurrentUser: vi.fn(),
  requestUploadUrl: vi.fn(),
  uploadFile: vi.fn(),
  startRun: vi.fn(),
  getRunStatus: vi.fn(),
}));

function makeFile() {
  return new File(["print('hi')"], "pipeline.py", { type: "text/x-python" });
}

beforeEach(() => {
  pushMock.mockClear();
  vi.mocked(api.getCurrentUser).mockResolvedValue({ id: "1", email: "alice@example.com" });
  vi.mocked(api.requestUploadUrl).mockResolvedValue({
    upload_url: "https://seaweedfs.example/alice/proj1/script.py",
  });
  vi.mocked(api.uploadFile).mockResolvedValue(undefined);
  vi.mocked(api.startRun).mockResolvedValue({ run_id: "run-123" });
  vi.mocked(api.getRunStatus).mockResolvedValue({
    stage: "queued",
    result: null,
    error: null,
  });
});

describe("ChatPage authentication", () => {
  it("redirects to /login when the session is invalid", async () => {
    vi.mocked(api.getCurrentUser).mockRejectedValue(new api.ApiError(401, "Not authenticated"));

    render(<ChatPage />);

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/login");
    });
  });

  it("shows the derived username with no username field once authenticated", async () => {
    render(<ChatPage />);

    expect(await screen.findByText("alice", { exact: false })).toBeInTheDocument();
    expect(screen.queryByLabelText("Username")).not.toBeInTheDocument();
  });
});

describe("ChatPage send gating", () => {
  it("disables preset prompt chips when project or file are missing", async () => {
    render(<ChatPage />);

    expect(await screen.findByRole("button", { name: "Explain this pipeline" })).toBeDisabled();
  });

  it("enables preset prompt chips once project and a file are present", async () => {
    render(<ChatPage />);
    const user = userEvent.setup();

    await user.type(await screen.findByLabelText("Project"), "proj1");
    await user.upload(screen.getByLabelText("Attach file"), makeFile());

    expect(screen.getByRole("button", { name: "Explain this pipeline" })).toBeEnabled();
  });
});

describe("ChatPage preset prompt send", () => {
  it("sends the preset's exact text with the current project", async () => {
    render(<ChatPage />);
    const user = userEvent.setup();
    const file = makeFile();

    await user.type(await screen.findByLabelText("Project"), "proj1");
    await user.upload(screen.getByLabelText("Attach file"), file);
    await user.click(screen.getByRole("button", { name: "Explain this pipeline" }));

    expect(api.requestUploadUrl).toHaveBeenCalledWith("proj1");
    expect(api.uploadFile).toHaveBeenCalledWith(
      "https://seaweedfs.example/alice/proj1/script.py",
      file
    );
    expect(api.startRun).toHaveBeenCalledWith("proj1", "Explain this pipeline");
  });
});
