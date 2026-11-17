import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

// The click test calls the component as a function, outside a React render, so useId
// is replaced with a fixed id.
vi.mock("react", async (original) => ({
  ...(await original<typeof import("react")>()),
  useId: () => "q-eu-nexus",
}));

import type { NullableBoolean } from "../lib/types";
import { TriStateControl } from "./tri-state-control";

function markup(value: NullableBoolean): string {
  return renderToStaticMarkup(<TriStateControl label="EU nexus" value={value} onChange={() => {}} />);
}

function pressed(html: string): string[] {
  return [...html.matchAll(/<button aria-pressed="true"[^>]*>([^<]+)<\/button>/g)].map((m) => m[1]);
}

describe("TriStateControl", () => {
  it("is a group labelled by its question", () => {
    const html = markup(true);
    expect(html).toContain('<div class="triState" role="group" aria-labelledby="q-eu-nexus">');
    expect(html).toContain('<span id="q-eu-nexus">EU nexus</span>');
  });

  it.each<[NullableBoolean, string]>([
    [true, "Yes"],
    [false, "No"],
    [null, "Review"],
  ])("marks only the button for %s as pressed", (value, label) => {
    const html = markup(value);
    expect(pressed(html)).toEqual([label]);
    expect(html.match(/aria-pressed="false"/g)).toHaveLength(2);
  });

  it("answers with the value of the button clicked", () => {
    const onChange = vi.fn();
    const element = TriStateControl({ label: "EU nexus", value: true, onChange }) as unknown as {
      props: { children: [unknown, { props: { children: Array<{ props: { onClick: () => void } }> } }] };
    };
    const buttons = element.props.children[1].props.children;
    buttons.forEach((button) => button.props.onClick());
    expect(onChange.mock.calls).toEqual([[true], [false], [null]]);
  });
});
