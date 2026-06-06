import { useEffect, useState } from "react";

import { getActiveTheme, type Theme } from "@/lib/theme";

// Subscribe a component to live theme changes. The theme is a `.dark` class on
// <html> toggled outside React (ThemeToggle + the no-FOUC init script), so we
// observe the class attribute and re-render on change. Returns "light" until
// mounted (SSR-safe). Use where rendering must react to the theme — e.g. the
// Leaflet map, whose tiles + marker colours are otherwise mount-time snapshots.
export function useTheme(): Theme {
  const [theme, setTheme] = useState<Theme>("light");
  useEffect(() => {
    setTheme(getActiveTheme());
    const observer = new MutationObserver(() => setTheme(getActiveTheme()));
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => observer.disconnect();
  }, []);
  return theme;
}
