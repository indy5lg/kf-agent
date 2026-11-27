import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RunOutcome } from "./RunOutcome";

describe("RunOutcome", () => {
  it("shows a text result as plain text under 'Run succeeded'", () => {
    render(<RunOutcome status={{ stage: "succeeded", result: "Model trained", error: null }} />);

    expect(screen.getByText("Run succeeded")).toBeInTheDocument();
    expect(screen.getByText("Model trained")).toBeInTheDocument();
  });

  it("shows a structured result as indented JSON under 'Run succeeded'", () => {
    const result = { accuracy: 0.93, epochs: [1, 2] };
    const { container } = render(
      <RunOutcome status={{ stage: "succeeded", result, error: null }} />
    );

    expect(screen.getByText("Run succeeded")).toBeInTheDocument();
    expect(container.querySelector("pre")?.textContent).toBe(JSON.stringify(result, null, 2));
  });

  it("shows the error under 'Run failed'", () => {
    render(<RunOutcome status={{ stage: "failed", result: null, error: "Script has no pipeline" }} />);

    expect(screen.getByText("Run failed")).toBeInTheDocument();
    expect(screen.getByText("Script has no pipeline")).toBeInTheDocument();
  });
});
