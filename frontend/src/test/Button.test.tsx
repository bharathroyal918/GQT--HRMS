import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "../components/ui/Button";

describe("Button UI Primitive", () => {
  it("renders with children text", () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("handles onClick callback", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Submit</Button>);
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("disables button and shows spinner when isLoading is true", () => {
    render(<Button isLoading>Processing</Button>);
    const btn = screen.getByRole("button");
    expect(btn).toBeDisabled();
    expect(screen.getByTestId("button-spinner")).toBeInTheDocument();
  });

  it("applies primary brand navy classes by default", () => {
    render(<Button>Brand Button</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("bg-brand-navy");
  });
});
