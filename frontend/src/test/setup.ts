import "@testing-library/jest-dom";
import { vi } from "vitest";

// Mock matchMedia for responsive UI components
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => { },
    removeListener: () => { },
    addEventListener: () => { },
    removeEventListener: () => { },
    dispatchEvent: () => false,
  }),
});

// Suppress unhandled network rejections during mock test render
vi.mock("../api/apiClient", () => ({
  apiClient: {
    get: vi.fn().mockRejectedValue({ response: { status: 401 } }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));
