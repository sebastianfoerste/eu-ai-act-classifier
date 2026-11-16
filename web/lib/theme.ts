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

function isChoice(theme: unknown): theme is "light" | "dark" {
  return theme === "light" || theme === "dark";
}

// The choice the page shows now: data-theme on the root element, or the system setting.
// The button cycles from this, so it is right with blocked storage and after another
// tab changed the choice.
export function shownTheme(root: Root): Theme {
  const theme = root.dataset.theme;
  return isChoice(theme) ? theme : "system";
}

// Sets or clears data-theme on the root element. globals.css shows the matching name
// in the Theme button from that attribute, so the label is right before hydration.
export function showTheme(root: Root, theme: Theme): void {
  if (isChoice(theme)) root.dataset.theme = theme;
  else delete root.dataset.theme;
}

// Shows the choice and stores it. Where storage is blocked the page still switches for
// this visit.
export function applyTheme(root: Root, storage: Store | null, theme: Theme): void {
  showTheme(root, theme);
  try {
    if (isChoice(theme)) storage?.setItem(THEME_KEY, theme);
    else storage?.removeItem(THEME_KEY);
  } catch {
    // Not stored.
  }
}

// Sets a stored light or dark again when the button mounts, because React's development
// remount resets the attributes of <html>. A read of "system" changes nothing: with
// blocked storage every read is "system", and clearing the attribute on each route
// would drop a choice made on this visit.
export function restoreTheme(root: Root, storage: Store | null): void {
  const stored = readTheme(storage);
  if (stored !== "system") showTheme(root, stored);
}

// One click on the button: the next choice, shown and stored.
export function cycleTheme(root: Root, storage: Store | null): Theme {
  const next = nextTheme(shownTheme(root));
  applyTheme(root, storage, next);
  return next;
}

export function themeAnnouncement(theme: Theme): string {
  return `Theme set to ${THEME_LABELS[theme]}`;
}

type StorageEvents = {
  addEventListener(type: "storage", listener: (event: { key: string | null }) => void): void;
  removeEventListener(type: "storage", listener: (event: { key: string | null }) => void): void;
};

// Shows a choice made in another tab. A storage event with key null means the storage
// was cleared. Returns the function that stops listening.
export function watchTheme(
  events: StorageEvents,
  root: Root,
  storage: () => Store | null,
  onChange: () => void,
): () => void {
  const listener = (event: { key: string | null }) => {
    if (event.key !== null && event.key !== THEME_KEY) return;
    showTheme(root, readTheme(storage()));
    onChange();
  };
  events.addEventListener("storage", listener);
  return () => events.removeEventListener("storage", listener);
}
