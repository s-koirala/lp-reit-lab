// Light/dark theme management for the static SPA.
//
// No `next-themes` dependency — this is TanStack Start, not Next. The theme is a
// single `.dark` class on <html> (see the `@custom-variant dark` in styles.css).
// THEME_INIT_SCRIPT applies it synchronously in <head> before first paint to
// avoid a flash of the wrong theme; the toggle then flips the class at runtime
// and persists the choice to localStorage.

export type Theme = "light" | "dark";

export const THEME_STORAGE_KEY = "theme";

// Inline <head> script (runs before React hydrates): use the stored choice if
// present, else fall back to the OS `prefers-color-scheme`. Serialised to a
// string so it can run via dangerouslySetInnerHTML. Wrapped in try/catch so a
// blocked localStorage (private mode) degrades to the OS preference.
export const THEME_INIT_SCRIPT =
  `(function(){try{` +
  `var k=${JSON.stringify(THEME_STORAGE_KEY)};` +
  `var s=localStorage.getItem(k);` +
  `var d=s?s==="dark":matchMedia("(prefers-color-scheme: dark)").matches;` +
  `document.documentElement.classList.toggle("dark",d);` +
  `}catch(e){}})();`;

/** The theme currently applied to <html>. Returns "light" during SSR. */
export function getActiveTheme(): Theme {
  if (typeof document === "undefined") return "light";
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

/** Apply a theme to <html> and persist it. No-op during SSR. */
export function applyTheme(theme: Theme): void {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", theme === "dark");
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Storage unavailable; the class still applies for this session.
  }
}

/** Flip light<->dark, persist, and return the new theme. Client-only. */
export function toggleTheme(): Theme {
  if (typeof document === "undefined") return "light";
  const next: Theme = getActiveTheme() === "dark" ? "light" : "dark";
  applyTheme(next);
  return next;
}
