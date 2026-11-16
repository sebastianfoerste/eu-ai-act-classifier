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

const isChoice = theme => theme === "light" || theme === "dark";

// The choice the page shows now: data-theme on the root element, or the system setting.
// The button cycles from this, so it is right with blocked storage and after another
// tab changed the choice.
export const shownTheme = root => (isChoice(root.dataset.theme) ? root.dataset.theme : "system");

// Sets or clears data-theme on the root element. The stylesheet shows the matching
// name in the Theme button from that attribute, so the label needs no script.
export function showTheme(root, theme) {
  if (isChoice(theme)) root.dataset.theme = theme;
  else delete root.dataset.theme;
}

// Shows the choice and stores it. Where storage is blocked the page still switches
// for this visit.
export function applyTheme(root, storage, theme) {
  showTheme(root, theme);
  try {
    if (isChoice(theme)) storage?.setItem(THEME_KEY, theme);
    else storage?.removeItem(THEME_KEY);
  } catch { /* not stored */ }
}

// Wires the Theme button. A click moves to the next choice and names it in the status
// element, which is a live region. A choice made in another tab arrives as a storage
// event (key null: storage was cleared) and is shown without an announcement.
export function wireThemeToggle({ root, button, status, storage, events }) {
  button.addEventListener("click", () => {
    const next = nextTheme(shownTheme(root));
    applyTheme(root, storage(), next);
    status.textContent = `Theme set to ${THEME_LABELS[next]}`;
  });
  events.addEventListener("storage", event => {
    if (event.key !== null && event.key !== THEME_KEY) return;
    showTheme(root, readTheme(storage()));
    status.textContent = "";
  });
}
