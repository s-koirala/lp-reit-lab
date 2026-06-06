import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";
import tailwindcss from "@tailwindcss/vite";
import tsConfigPaths from "vite-tsconfig-paths";
import viteReact from "@vitejs/plugin-react";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";

// De-Lovabled config (P1, see web/PROVENANCE.md).
//
// Replaces @lovable.dev/vite-tanstack-config with the standard plugin stack it
// wrapped. Dropped, because they were Lovable-platform-only and never ran in a
// production/CI build (all are apply:"serve" and/or sandbox-gated):
//   - componentTagger (lovable-tagger) — dev DOM tagging for the Lovable editor
//   - dev SSR / server-fn error loggers — pushed errors over HMR to the editor
//     (our src/server.ts + src/start.ts already own SSR error handling)
//   - hmr-gate + dev-server bridge — Lovable sandbox HMR plumbing
//   - sandbox host/port coercion (::, 8080) and watch-debounce defaults
// Replicated 1:1 for the non-sandbox path: tailwindcss, vite-tsconfig-paths,
// tanstackStart (client import-protection default + our SSR entry), React,
// the "@" alias, the React/Query dedupe list, and VITE_* env exposure.

export default defineConfig(async ({ command, mode }) => {
  // Mirror the wrapper: expose VITE_-prefixed vars on import.meta.env. Empty
  // (hence a no-op) unless a .env defines VITE_* keys.
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const define = Object.fromEntries(
    Object.entries(env).map(([k, v]) => [`import.meta.env.${k}`, JSON.stringify(v)]),
  );

  const plugins = [
    tailwindcss(),
    tsConfigPaths({ projects: ["./tsconfig.json"] }),
    tanstackStart({
      importProtection: {
        behavior: "error",
        client: { files: ["**/server/**"], specifiers: ["server-only"] },
      },
      // Route the bundled server entry to src/server.ts (our SSR error wrapper).
      server: { entry: "server" },
    }),
  ];

  // Optional deploy build. The wrapper only ran Nitro inside the Lovable sandbox;
  // outside it the local build emitted dist/client + dist/server with no Nitro.
  // We preserve that default and make the Cloudflare target opt-in via env, so
  // the standard `bun run build` output stays byte-for-byte comparable.
  if (command === "build" && process.env.NITRO_PRESET) {
    const { nitro } = await import("nitro/vite");
    const preset = process.env.NITRO_PRESET;
    plugins.push(
      nitro({
        preset,
        output: { dir: "dist", serverDir: "dist/server", publicDir: "dist/client" },
        ...(preset === "cloudflare-module"
          ? { cloudflare: { nodeCompat: true, deployConfig: true } }
          : {}),
      }),
    );
  }

  // React lands after the (optional) Nitro plugin, matching the wrapper's order.
  plugins.push(viteReact());

  return {
    define,
    resolve: {
      alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
      dedupe: [
        "react",
        "react-dom",
        "react/jsx-runtime",
        "react/jsx-dev-runtime",
        "@tanstack/react-query",
        "@tanstack/query-core",
      ],
    },
    plugins,
  };
});
