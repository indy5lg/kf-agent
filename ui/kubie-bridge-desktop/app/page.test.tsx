import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LandingPage from "./page";

afterEach(() => {
  vi.useRealTimers();
});

describe("Landing page content", () => {
  it("shows the Kubie-Bridge name", () => {
    render(<LandingPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Kubie-Bridge" })
    ).toBeInTheDocument();
  });

  it("lists each team member", () => {
    render(<LandingPage />);
    for (const name of [
      "Elvin Pineda",
      "Santiago Acosta Rodriguez",
      "Andres Ferrer",
    ]) {
      expect(screen.getByText(name)).toBeInTheDocument();
    }
  });

  it("links into the app at /chat", () => {
    render(<LandingPage />);
    expect(screen.getByRole("link", { name: "Get started" })).toHaveAttribute(
      "href",
      "/chat"
    );
  });

  it("does not include a login form", () => {
    const { container } = render(<LandingPage />);
    expect(container.querySelector('input[type="password"]')).toBeNull();
    expect(screen.queryByRole("textbox")).toBeNull();
  });
});

describe("Landing page slideshow", () => {
  function currentSlideTitle() {
    return screen.getByRole("heading", { level: 2 }).textContent;
  }

  it("starts on the first slide", () => {
    render(<LandingPage />);
    expect(currentSlideTitle()).toBe("What is Kubie-Bridge?");
  });

  it("moves forward and back with the arrow buttons, wrapping around", async () => {
    render(<LandingPage />);
    const user = userEvent.setup();
    const first = currentSlideTitle();

    await user.click(screen.getByRole("button", { name: "Next slide" }));
    expect(currentSlideTitle()).not.toBe(first);

    await user.click(screen.getByRole("button", { name: "Previous slide" }));
    expect(currentSlideTitle()).toBe(first);

    await user.click(screen.getByRole("button", { name: "Previous slide" }));
    const dots = screen.getAllByRole("button", { name: /Go to slide/ });
    expect(dots[dots.length - 1]).toHaveAttribute("aria-current", "true");
  });

  it("jumps to a slide when its dot is clicked", async () => {
    render(<LandingPage />);
    const user = userEvent.setup();
    const dots = screen.getAllByRole("button", { name: /Go to slide/ });

    await user.click(dots[2]);
    expect(dots[2]).toHaveAttribute("aria-current", "true");
    expect(dots[0]).not.toHaveAttribute("aria-current", "true");
  });

  it("advances automatically every 5 seconds", () => {
    vi.useFakeTimers();
    render(<LandingPage />);
    const first = currentSlideTitle();

    act(() => {
      vi.advanceTimersByTime(4999);
    });
    expect(currentSlideTitle()).toBe(first);

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(currentSlideTitle()).not.toBe(first);
  });
});
