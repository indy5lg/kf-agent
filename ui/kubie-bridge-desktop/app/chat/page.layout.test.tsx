import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act, within } from "@testing-library/react";
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
  logout: vi.fn(),
  requestUploadUrl: vi.fn(),
  uploadFile: vi.fn(),
  startRun: vi.fn(),
  getRunStatus: vi.fn(),
}));

const POLL_INTERVAL_MS = 2000;

function makeFile() {
  return new File(["print('hi')"], "pipeline.py", { type: "text/x-python" });
}

function setup() {
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

async function startARun(user: ReturnType<typeof setup>) {
  await user.type(await screen.findByLabelText("Project"), "proj1");
  await user.upload(screen.getByLabelText("Attach file"), makeFile());
  await user.click(screen.getByRole("button", { name: "Explain this pipeline" }));
}

async function poll(times = 1) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS * times);
  });
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  pushMock.mockClear();
  vi.mocked(api.getCurrentUser).mockResolvedValue({ id: "1", email: "alice@example.com" });
  vi.mocked(api.logout).mockResolvedValue(undefined);
  vi.mocked(api.requestUploadUrl).mockResolvedValue({
    upload_url: "https://seaweedfs.example/alice/proj1/script.py",
  });
  vi.mocked(api.uploadFile).mockResolvedValue(undefined);
  vi.mocked(api.startRun).mockResolvedValue({ run_id: "run-123" });
  vi.mocked(api.getRunStatus).mockResolvedValue({ stage: "running", result: null, error: null });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("Upload page header", () => {
  it("shows the wordmark, the username and a log out button", async () => {
    render(<ChatPage />);

    const header = await screen.findByRole("banner");
    expect(within(header).getByText("Kubie-Bridge")).toBeInTheDocument();
    expect(within(header).getByText("alice")).toBeInTheDocument();
    expect(within(header).getByRole("button", { name: "Log out" })).toBeInTheDocument();
  });

  it("navigates to /login after a successful log out", async () => {
    render(<ChatPage />);

    await setup().click(await screen.findByRole("button", { name: "Log out" }));

    expect(api.logout).toHaveBeenCalledOnce();
    expect(pushMock).toHaveBeenCalledWith("/login");
  });

  it("stays on the page and reports a failed log out", async () => {
    vi.mocked(api.logout).mockRejectedValue(new Error("network down"));
    render(<ChatPage />);

    await setup().click(await screen.findByRole("button", { name: "Log out" }));

    expect(await screen.findByText("Could not log out. Please try again.")).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalled();
  });
});

describe("Upload page preset buttons", () => {
  it("names each preset button exactly by its preset text", async () => {
    render(<ChatPage />);
    await screen.findByLabelText("Project");

    for (const prompt of api.PRESET_PROMPTS) {
      expect(screen.getByRole("button", { name: prompt })).toHaveAccessibleName(prompt);
    }
  });
});

describe("Upload page processing cube", () => {
  it("is not shown before a run is started", async () => {
    render(<ChatPage />);
    await screen.findByLabelText("Project");

    expect(screen.queryByTestId("processing-cube")).not.toBeInTheDocument();
  });

  it("is shown with the stage text while the run is in progress", async () => {
    render(<ChatPage />);
    await startARun(setup());
    await poll();

    expect(screen.getByTestId("processing-cube")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
  });

  it("is replaced by a 'Run succeeded' card once the run succeeds", async () => {
    render(<ChatPage />);
    await startARun(setup());
    await poll();
    vi.mocked(api.getRunStatus).mockResolvedValue({
      stage: "succeeded",
      result: { accuracy: 0.9 },
      error: null,
    });
    await poll();

    expect(screen.queryByTestId("processing-cube")).not.toBeInTheDocument();
    expect(screen.getByText("Run succeeded")).toBeInTheDocument();
  });

  it("is replaced by a 'Run failed' card once the run fails", async () => {
    render(<ChatPage />);
    await startARun(setup());
    await poll();
    vi.mocked(api.getRunStatus).mockResolvedValue({
      stage: "failed",
      result: null,
      error: "Script has no pipeline",
    });
    await poll();

    expect(screen.queryByTestId("processing-cube")).not.toBeInTheDocument();
    expect(screen.getByText("Run failed")).toBeInTheDocument();
    expect(screen.getByText("Script has no pipeline")).toBeInTheDocument();
  });

  it("is hidden once polling gives up on the run", async () => {
    render(<ChatPage />);
    await startARun(setup());
    vi.mocked(api.getRunStatus).mockRejectedValue(new Error("unreachable"));
    await poll(5);

    expect(screen.queryByTestId("processing-cube")).not.toBeInTheDocument();
  });
});
