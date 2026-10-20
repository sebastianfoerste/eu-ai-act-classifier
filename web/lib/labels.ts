// Display labels generated from src/eu_ai_act_classifier/labels.py by
// scripts/build_playground.py. The cockpit holds no label wording of its own
// for values the classifier defines.
import catalog from "./labels.json";

export type LabelNamespace = keyof typeof catalog.namespaces;

const namespaces = catalog.namespaces as Record<LabelNamespace, Record<string, string>>;

// Fallback for workflow values the classifier does not label (inventory
// statuses, connector states): "review_required" -> "Review Required".
export function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replaceAll(".", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function labelFor(namespace: LabelNamespace, value: string): string {
  return namespaces[namespace][value] ?? formatLabel(value);
}
