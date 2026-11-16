// The cockpit's colour-scheme choice. The inline script in app/layout.tsx applies a stored
// choice before the first paint; components/theme-toggle.tsx changes it.
export const THEME_KEY = "eu-ai-act-classifier.theme";
export const THEMES = ["system", "light", "dark"] as const;
export type Theme = (typeof THEMES)[number];
export const THEME_LABELS: Record<Theme, string> = {
  system: "System",
  light: "Light",
  dark: "Dark",
};

type Store = Pick<Storage, "getItem" | "setItem" | "removeItem">;
type Root = { dataset: Record<string, string | undefined> };

// Runs while the HTML is parsed, so a stored choice applies before the first paint.
export const THEME_INIT_SCRIPT = `(function(){try{var t=window.localStorage.getItem(${JSON.stringify(THEME_KEY)});if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}})()`;

// Storage can be blocked, and reading the property itself then throws.
export function browserStorage(): Store | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

// Only a stored "light" or "dark" overrides the system setting.
export function readTheme(storage: Store | null): Theme {
  try {
    const value = storage?.getItem(THEME_KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch {
    return "system";
  }
}

export function nextTheme(theme: Theme): Theme {
  return THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];
}

// Sets or clears data-theme on the root element and stores the choice. Where storage is
// blocked the page still switches for this visit.
export function applyTheme(root: Root, storage: Store | null, theme: Theme): void {
  if (theme === "system") delete root.dataset.theme;
  else root.dataset.theme = theme;
  try {
    if (theme === "system") storage?.removeItem(THEME_KEY);
    else storage?.setItem(THEME_KEY, theme);
  } catch {
    // Not stored.
  }
}
