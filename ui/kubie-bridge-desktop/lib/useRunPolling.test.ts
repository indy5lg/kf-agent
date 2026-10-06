import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useRunPolling } from "./useRunPolling";
import * as api from "./api";

vi.mock("./api", () => ({
  getRunStatus: vi.fn(),
}));

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("useRunPolling", () => {
  it("polls every 2 seconds and stops once a terminal stage is returned", async () => {
    const getRunStatus = vi.mocked(api.getRunStatus);
    getRunStatus
      .mockResolvedValueOnce({ stage: "running", result: null, error: null })
      .mockResolvedValueOnce({ stage: "succeeded", result: { ok: true }, error: null });

    renderHook(() => useRunPolling("run-1"));

    await vi.advanceTimersByTimeAsync(2000);
    expect(getRunStatus).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(2000);
    expect(getRunStatus).toHaveBeenCalledTimes(2);

    await vi.advanceTimersByTimeAsync(2000);
    expect(getRunStatus).toHaveBeenCalledTimes(2);
  });

  it("stops with an error state after 5 consecutive failed polls", async () => {
    const getRunStatus = vi.mocked(api.getRunStatus);
    getRunStatus.mockRejectedValue(new Error("network error"));

    const { result } = renderHook(() => useRunPolling("run-1"));

    for (let i = 0; i < 5; i++) {
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });
    }

    expect(getRunStatus).toHaveBeenCalledTimes(5);
    expect(result.current.pollingFailed).toBe(true);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(getRunStatus).toHaveBeenCalledTimes(5);
  });
});
