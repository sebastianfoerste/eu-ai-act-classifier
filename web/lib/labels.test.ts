import { describe, expect, it } from "vitest";
import { formatLabel, labelFor } from "./labels";

describe("labelFor", () => {
  it("uses the classifier's catalog for Annex III points", () => {
    expect(labelFor("annex_iii_area", "III.5.b")).toBe(
      "Annex III(5)(b): Creditworthiness evaluation and credit scoring",
    );
  });

  it("labels review statuses and artifacts from the catalog", () => {
    expect(labelFor("review_status", "review_required")).toBe("Review required");
    expect(labelFor("artifacts", "fria")).toBe("Fundamental rights impact assessment (Art. 27)");
  });

  it("falls back to a readable label for values outside the catalog", () => {
    expect(labelFor("roles", "custom_role")).toBe(formatLabel("custom_role"));
    expect(formatLabel("draft_only")).toBe("Draft Only");
  });
});
