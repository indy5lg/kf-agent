import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthForm } from "./AuthForm";

function renderAuthForm(onSubmit = vi.fn().mockResolvedValue(undefined)) {
  render(
    <AuthForm
      title="Log in"
      submitLabel="Log in"
      loadingLabel="Logging in..."
      onSubmit={onSubmit}
      footer={null}
    />
  );
  return { onSubmit };
}

describe("AuthForm branding", () => {
  it("renders the Kubie wordmark in its branding header", () => {
    renderAuthForm();
    expect(screen.getByText("Kubie")).toBeInTheDocument();
  });

  it("renders a placeholder mark alongside the Kubie wordmark", () => {
    renderAuthForm();
    expect(screen.getByTestId("kubie-mark")).toBeInTheDocument();
  });
});

describe("AuthForm submit behavior", () => {
  it("still calls onSubmit with the entered email and password", async () => {
    const { onSubmit } = renderAuthForm();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Email"), "person@example.com");
    await user.type(screen.getByLabelText("Password"), "hunter2");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(onSubmit).toHaveBeenCalledWith("person@example.com", "hunter2");
  });
});
