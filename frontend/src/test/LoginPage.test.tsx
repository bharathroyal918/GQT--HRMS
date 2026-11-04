import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { LoginPage } from "../pages/LoginPage";
import { AuthProvider } from "../context/AuthContext";

describe("LoginPage Component", () => {
  it("renders login form with brand logo and fields", () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByRole("heading", { name: /gqt recruitment crm/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/corporate email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in to hrms/i })).toBeInTheDocument();
  });
});
