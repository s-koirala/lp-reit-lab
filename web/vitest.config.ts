import { defineConfig } from "vitest/config";

// Standalone Vitest config — deliberately does NOT extend vite.config.ts, so the
// TanStack Start / Nitro plugins (build-time, app-server oriented) don't load for
// unit tests. The engine parity tests are pure TS + JSON, run in a node env.
export default defineConfig({
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
