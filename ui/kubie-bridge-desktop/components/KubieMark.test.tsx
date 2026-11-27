import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { KubieMark } from "./KubieMark";

describe("KubieMark", () => {
  it("renders the placeholder mark without an image file", () => {
    const { container } = render(<KubieMark />);
    expect(screen.getByTestId("kubie-mark")).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
  });
});
