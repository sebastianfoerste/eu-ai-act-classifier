import { readFileSync } from "node:fs";
import type { ReactElement, ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { THEME_INIT_SCRIPT, THEME_KEY } from "../lib/theme";

// The repository has no DOM test environment and adds no dependency for one. These tests
// call the component as a function with two React hooks replaced: state lives in `state`
// (calling the component again is the re-render) and the layout effect runs at once.
const state = vi.hoisted(() => ({ value: undefined as unknown, set: false, cleanups: [] as Array<() => void> }));
vi.mock("react", async (original) => ({
  ...(await original<typeof import("react")>()),
  useState: (initial: unknown) => [
    state.set ? state.value : initial,
    (next: unknown) => {
      state.value = next;
      state.set = true;
    },
  ],
  useLayoutEffect: (effect: () => void | (() => void)) => {
    const cleanup = effect();
    if (cleanup) state.cleanups.push(cleanup);
  },
}));

import { ThemeToggle } from "./theme-toggle";

type Listener = (event: { key: string | null }) => void;
type Props = { children?: ReactNode; onClick?: () => void; role?: string };

function fakeBrowser(stored: Record<string, string> | "blocked") {
  const data = new Map(Object.entries(stored === "blocked" ? {} : stored));
  const listeners = new Set<Listener>();
  // Each read of window.localStorage returns a new object, so the record of storage
  // calls lives here, next to the data.
  const calls: string[] = [];
  const document = { documentElement: { dataset: {} as Record<string, string | undefined> } };
  const window = {
    get localStorage() {
      if (stored === "blocked") throw new Error("blocked");
      return {
        getItem: (key: string) => (calls.push("getItem"), data.get(key) ?? null),
        setItem: (key: string, value: string) => (calls.push("setItem"), void data.set(key, value)),
        removeItem: (key: string) => (calls.push("removeItem"), void data.delete(key)),
      };
    },
    addEventListener: (_type: string, listener: Listener) => void listeners.add(listener),
    removeEventListener: (_type: string, listener: Listener) => void listeners.delete(listener),
  };
  vi.stubGlobal("document", document);
  vi.stubGlobal("window", window);
  return {
    data,
    calls,
    listeners,
    window,
    document,
    dataset: document.documentElement.dataset,
    root: document.documentElement,
  };
}

// One render: the button and the status element of the fragment the component returns.
function render() {
  const fragment = ThemeToggle() as ReactElement<Props>;
  const [button, status] = fragment.props.children as Array<ReactElement<Props>>;
  return { click: () => button.props.onClick?.(), button, announcement: status.props.children, status };
}

beforeEach(() => {
  state.value = undefined;
  state.set = false;
  state.cleanups = [];
});
afterEach(() => vi.unstubAllGlobals());

describe("ThemeToggle", () => {
  it("renders all three names and an empty, visually hidden status element", () => {
    fakeBrowser({});
    expect(renderToStaticMarkup(<ThemeToggle />)).toBe(
      '<button class="secondaryButton themeToggle" type="button"><span>Theme: ' +
        '<span class="themeName" data-theme-name="system">System</span>' +
        '<span class="themeName" data-theme-name="light">Light</span>' +
        '<span class="themeName" data-theme-name="dark">Dark</span>' +
        "</span></button>" +
        '<span class="visuallyHidden" role="status"></span>',
    );
  });

  it("shows the name that matches data-theme through the stylesheet alone", () => {
    const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
    expect(css).toMatch(/\.themeName \{\s*display: none;\s*\}/);
    expect(css).toMatch(
      /:root:not\(\[data-theme="light"\]\):not\(\[data-theme="dark"\]\) \.themeName\[data-theme-name="system"\],\s*:root\[data-theme="light"\] \.themeName\[data-theme-name="light"\],\s*:root\[data-theme="dark"\] \.themeName\[data-theme-name="dark"\] \{\s*display: inline;\s*\}/,
    );
    expect(css).toMatch(/\.visuallyHidden \{[^}]*clip-path: inset\(50%\);[^}]*position: absolute;/);
  });

  it("cycles, stores and announces the choice on each click", () => {
    const browser = fakeBrowser({});
    expect(render().announcement).toBe("");
    render().click();
    expect(browser.dataset).toEqual({ theme: "light" });
    expect(browser.data.get(THEME_KEY)).toBe("light");
    expect(render().announcement).toBe("Theme set to Light");
    render().click();
    expect(browser.dataset).toEqual({ theme: "dark" });
    expect(render().announcement).toBe("Theme set to Dark");
    render().click();
    expect(browser.dataset).toEqual({});
    expect(browser.data.size).toBe(0);
    const { status, announcement } = render();
    expect(announcement).toBe("Theme set to System");
    expect(status.props.role).toBe("status");
  });

  it("sets a stored choice again on mount and cycles from it", () => {
    const browser = fakeBrowser({ [THEME_KEY]: "dark" });
    const { click } = render();
    expect(browser.dataset).toEqual({ theme: "dark" });
    click();
    expect(browser.dataset).toEqual({});
    expect(render().announcement).toBe("Theme set to System");
  });

  // The inline script of the layout, then the button's mount: two reads, no write, and a
  // value the page does not understand stays where it is.
  it.each<Record<string, string>>([{}, { [THEME_KEY]: "dark" }, { [THEME_KEY]: "light" }, { [THEME_KEY]: "sepia" }])(
    "a page load only reads the stored choice: %j",
    (stored) => {
      const browser = fakeBrowser(stored);
      new Function("window", "document", THEME_INIT_SCRIPT)(browser.window, browser.document);
      render();
      expect(browser.calls).toEqual(["getItem", "getItem"]);
      expect(Object.fromEntries(browser.data)).toEqual(stored);
    },
  );

  it("keeps a choice across mounts when storage is blocked", () => {
    const browser = fakeBrowser("blocked");
    render().click();
    render().click();
    expect(browser.dataset).toEqual({ theme: "dark" });
    // The next route mounts the button again. It must not fall back to the system setting.
    state.set = false;
    const { click, announcement } = render();
    expect(announcement).toBe("");
    expect(browser.dataset).toEqual({ theme: "dark" });
    click();
    expect(browser.dataset).toEqual({});
  });

  it("shows a choice from another tab without announcing it, and stops listening on unmount", () => {
    const browser = fakeBrowser({});
    render().click();
    expect(render().announcement).toBe("Theme set to Light");
    state.cleanups = [];
    render();
    browser.data.set(THEME_KEY, "dark");
    browser.listeners.forEach((listener) => listener({ key: THEME_KEY }));
    expect(browser.dataset).toEqual({ theme: "dark" });
    expect(render().announcement).toBe("");
    render().click();
    expect(browser.dataset).toEqual({});

    const before = browser.listeners.size;
    state.cleanups.splice(0).forEach((cleanup) => cleanup());
    expect(browser.listeners.size).toBeLessThan(before);
  });
});
