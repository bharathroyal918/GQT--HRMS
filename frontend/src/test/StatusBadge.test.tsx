import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "../components/ui/StatusBadge";

describe("StatusBadge Component", () => {
  it("renders status label", () => {
    render(<StatusBadge variant="success">Approved</StatusBadge>);
    expect(screen.getByText("Approved")).toBeInTheDocument();
  });

  it("applies variant styling", () => {
    const { container } = render(<StatusBadge variant="danger">Rejected</StatusBadge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("text-rose-700");
  });

  it("renders indicator dot when dot prop is true", () => {
    const { container } = render(
      <StatusBadge variant="warning" dot>
        Pending
      </StatusBadge>
    );
    const dot = container.querySelector("span.rounded-full");
    expect(dot).toBeInTheDocument();
  });
});
