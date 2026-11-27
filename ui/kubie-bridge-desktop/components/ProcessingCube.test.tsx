import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProcessingCube } from "./ProcessingCube";

describe("ProcessingCube", () => {
  it("is hidden from assistive technology", () => {
    render(<ProcessingCube />);
    expect(screen.getByTestId("processing-cube")).toHaveAttribute("aria-hidden", "true");
  });

  it("renders six cube faces", () => {
    render(<ProcessingCube />);
    expect(screen.getByTestId("processing-cube").querySelectorAll(".kubie-cube-face")).toHaveLength(6);
  });

  it("animates only when the system allows motion", () => {
    const { container } = render(<ProcessingCube />);
    const classes = Array.from(container.querySelectorAll("*")).flatMap((el) =>
      Array.from(el.classList)
    );
    const animationClasses = classes.filter((c) => c.includes("animate-cube-"));

    expect(animationClasses).toEqual(
      expect.arrayContaining(["motion-safe:animate-cube-hop", "motion-safe:animate-cube-tumble"])
    );
    for (const c of animationClasses) {
      expect(c.startsWith("motion-safe:")).toBe(true);
    }
  });
});
