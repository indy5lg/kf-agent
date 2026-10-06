import { describe, it, expect } from "vitest";
import { stageToCheckpoint } from "./stageProgress";

describe("stageToCheckpoint", () => {
  it("holds steady when the same stage is polled again", () => {
    const first = stageToCheckpoint("running");
    const second = stageToCheckpoint("running");

    expect(second).toBe(first);
  });

  it("advances when a later stage is polled", () => {
    const queued = stageToCheckpoint("queued");
    const validating = stageToCheckpoint("validating");
    const running = stageToCheckpoint("running");
    const finalizing = stageToCheckpoint("finalizing");
    const succeeded = stageToCheckpoint("succeeded");

    expect(validating).toBeGreaterThan(queued);
    expect(running).toBeGreaterThan(validating);
    expect(finalizing).toBeGreaterThan(running);
    expect(succeeded).toBeGreaterThan(finalizing);
  });
});
