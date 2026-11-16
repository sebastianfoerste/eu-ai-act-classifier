"use client";

import { useLayoutEffect, useState } from "react";
import {
  THEME_LABELS,
  type Theme,
  applyTheme,
  browserStorage,
  nextTheme,
  readTheme,
} from "../lib/theme";

export function ThemeToggle() {
  // "system" on the server and on the first client render, so hydration matches. The
  // stored choice is read in the layout effect, before the first paint after hydration.
  const [theme, setTheme] = useState<Theme>("system");

  useLayoutEffect(() => {
    const stored = readTheme(browserStorage());
    // React's development remount resets the attributes of <html>, so set it again.
    applyTheme(document.documentElement, browserStorage(), stored);
    setTheme(stored);
  }, []);

  function cycle() {
    const next = nextTheme(theme);
    applyTheme(document.documentElement, browserStorage(), next);
    setTheme(next);
  }

  return (
    <button className="secondaryButton themeToggle" type="button" onClick={cycle}>
      Theme: {THEME_LABELS[theme]}
    </button>
  );
}
