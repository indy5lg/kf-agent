import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UploadHeader } from "./UploadHeader";

describe("UploadHeader", () => {
  it("shows the wordmark, placeholder mark, username and a log out button", () => {
    render(<UploadHeader username="alice" onLogout={vi.fn()} />);

    expect(screen.getByText("Kubie-Bridge")).toBeInTheDocument();
    expect(screen.getByTestId("kubie-mark")).toBeInTheDocument();
    expect(screen.getByText("alice")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Log out" })).toBeInTheDocument();
  });

  it("calls onLogout when Log out is clicked", async () => {
    const onLogout = vi.fn();
    render(<UploadHeader username="alice" onLogout={onLogout} />);

    await userEvent.setup().click(screen.getByRole("button", { name: "Log out" }));

    expect(onLogout).toHaveBeenCalledOnce();
  });
});
