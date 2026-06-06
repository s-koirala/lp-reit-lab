import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { getActiveTheme, toggleTheme, type Theme } from "@/lib/theme";

// The server cannot know the visitor's stored/OS theme, so we render a stable
// placeholder until mount and only reflect the real state client-side. This
// keeps SSR markup deterministic and avoids a hydration mismatch; the actual
// initial class is set pre-paint by THEME_INIT_SCRIPT in __root.tsx.
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);
  useEffect(() => setTheme(getActiveTheme()), []);

  const isDark = theme === "dark";
  return (
    <button
      type="button"
      onClick={() => setTheme(toggleTheme())}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      aria-pressed={isDark}
      title={isDark ? "Light theme" : "Dark theme"}
      className="inline-flex h-8 w-8 items-center justify-center rounded-sm border border-rule text-muted-foreground transition-colors hover:text-foreground"
    >
      {theme === null ? (
        <span className="h-4 w-4" aria-hidden />
      ) : isDark ? (
        <Sun className="h-4 w-4" aria-hidden />
      ) : (
        <Moon className="h-4 w-4" aria-hidden />
      )}
    </button>
  );
}
