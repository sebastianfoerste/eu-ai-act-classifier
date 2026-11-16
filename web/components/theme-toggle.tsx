"use client";

import { useLayoutEffect, useState } from "react";
import {
  THEMES,
  THEME_LABELS,
  browserStorage,
  cycleTheme,
  restoreTheme,
  themeAnnouncement,
  watchTheme,
} from "../lib/theme";

export function ThemeToggle() {
  // The button renders all three names and globals.css shows the one that matches
  // data-theme on <html>. The inline script in the layout sets that attribute before the
  // first paint, so the label is right before hydration and the markup is the same on
  // the server and in the browser.
  const [announcement, setAnnouncement] = useState("");

  useLayoutEffect(() => {
    restoreTheme(document.documentElement, browserStorage());
    // A choice made in another tab is shown here and not announced.
    return watchTheme(window, document.documentElement, browserStorage, () => setAnnouncement(""));
  }, []);

  function cycle() {
    setAnnouncement(themeAnnouncement(cycleTheme(document.documentElement, browserStorage())));
  }

  return (
    <>
      <button className="secondaryButton themeToggle" type="button" onClick={cycle}>
        {/* One flex item, so the button's gap does not widen the space after the colon. */}
        <span>
          Theme:{" "}
          {THEMES.map((theme) => (
            <span className="themeName" data-theme-name={theme} key={theme}>
              {THEME_LABELS[theme]}
            </span>
          ))}
        </span>
      </button>
      <span className="visuallyHidden" role="status">
        {announcement}
      </span>
    </>
  );
}
