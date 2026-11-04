import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import { AuthProvider } from "../context/AuthContext";

describe("AppShell Layout Component", () => {
  it("renders header and navigation", () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <AppShell />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/hrms & recruitment crm/i)).toBeInTheDocument();
    expect(screen.getByText(/global quest technologies/i)).toBeInTheDocument();
  });
});
