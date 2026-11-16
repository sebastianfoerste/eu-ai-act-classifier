// The colour-scheme choice, shared by the page script and the regression tests.
// theme.js applies a stored choice before first paint and must use the same key.
export const THEME_KEY = "eu-ai-act-classifier.theme";
export const THEMES = ["system", "light", "dark"];
export const THEME_LABELS = { system: "System", light: "Light", dark: "Dark" };

// Only a stored "light" or "dark" overrides the system setting.
export function readTheme(storage) {
  try {
    const value = storage?.getItem(THEME_KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch { return "system"; }
}

export const nextTheme = theme => THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];

// Sets or clears data-theme on the root element and stores the choice. Where storage
// is blocked the page still switches for this visit.
export function applyTheme(root, storage, theme) {
  if (theme === "light" || theme === "dark") root.dataset.theme = theme;
  else delete root.dataset.theme;
  try {
    if (theme === "light" || theme === "dark") storage?.setItem(THEME_KEY, theme);
    else storage?.removeItem(THEME_KEY);
  } catch { /* not stored */ }
}
