import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import { baseProfile } from "../lib/samples";

/**
 * SystemProfile keys the cockpit deliberately offers no control for, each with the
 * reason. A key without a control leaves the profile at the blank default, so the
 * reviewer cannot set that fact at all. Empty: every key has a control.
 */
const HIDDEN_FIELDS: Record<string, string> = {};

/** The Art. 50 screens. The model types each one as bool, so null fails validation. */
const ART_50_FIELDS = [
  "interacts_with_natural_persons",
  "generates_synthetic_content",
  "deploys_emotion_or_biometric_categorisation",
  "generates_deepfakes",
];

function readSource(relativePath: string): string {
  return readFileSync(new URL(relativePath, import.meta.url), "utf8");
}

/** Drops block comments and whole-line comments, so a commented-out control does not count. */
function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
}

/** The keys of `export type SystemProfile = { ... }` in web/lib/types.ts. */
function systemProfileKeys(typesSource: string): string[] {
  const body = /export type SystemProfile = \{\n([\s\S]*?)\n\};/.exec(typesSource)?.[1];
  if (body === undefined) {
    throw new Error("export type SystemProfile not found in web/lib/types.ts");
  }
  return [...stripComments(body).matchAll(/^ {2}(\w+)\??:/gm)].map((match) => match[1]);
}

/** The profile keys the cockpit's controls write, read from their change handlers. */
function controlledKeys(cockpitSource: string): Set<string> {
  const keys = new Set<string>();
  for (const match of cockpitSource.matchAll(/=>\s*(?:updateProfile|toggleArray)\(\s*"(\w+)"/g)) {
    keys.add(match[1]);
  }
  if (/=>\s*updateDerogation\(/.test(cockpitSource)) {
    keys.add("derogation");
  }
  return keys;
}

/** The profile keys written by an on/off `<Toggle />`, which sends a boolean only. */
function toggleKeys(cockpitSource: string): Set<string> {
  const keys = new Set<string>();
  for (const element of cockpitSource.matchAll(/<Toggle\b([\s\S]*?)\/>/g)) {
    for (const match of element[1].matchAll(/=>\s*updateProfile\(\s*"(\w+)"/g)) {
      keys.add(match[1]);
    }
  }
  return keys;
}

describe("cockpit intake controls", () => {
  const profileKeys = systemProfileKeys(readSource("../lib/types.ts"));
  const cockpitSource = stripComments(readSource("./cockpit.tsx"));
  const controlled = controlledKeys(cockpitSource);

  it("reads every SystemProfile key from web/lib/types.ts", () => {
    expect(profileKeys).toEqual(expect.arrayContaining(Object.keys(baseProfile)));
    expect(new Set(profileKeys).size).toBe(profileKeys.length);
  });

  it("gives every SystemProfile key a control or a place on the hidden list", () => {
    const missing = profileKeys.filter((key) => !controlled.has(key) && !(key in HIDDEN_FIELDS));

    expect(missing).toEqual([]);
  });

  it("keeps the hidden list to SystemProfile keys that have no control", () => {
    for (const key of Object.keys(HIDDEN_FIELDS)) {
      expect(profileKeys).toContain(key);
      expect(controlled.has(key)).toBe(false);
    }
  });

  it("sets each Art. 50 screen with an on/off toggle", () => {
    const toggles = toggleKeys(cockpitSource);

    for (const key of ART_50_FIELDS) {
      expect(profileKeys).toContain(key);
      expect(toggles.has(key), `${key} has no <Toggle /> control`).toBe(true);
    }
  });
});
