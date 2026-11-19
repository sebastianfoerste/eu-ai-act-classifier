"use client";

import { useId } from "react";
import type { NullableBoolean } from "../lib/types";

const OPTIONS: Array<{ label: string; value: NullableBoolean }> = [
  { label: "Yes", value: true },
  { label: "No", value: false },
  { label: "Review", value: null },
];

/**
 * A yes, no or review answer to one question. The group carries the question for
 * assistive technology; aria-pressed carries the answer set, which the "active" class
 * shows only visually.
 */
export function TriStateControl({
  label,
  value,
  onChange,
}: {
  label: string;
  value: NullableBoolean;
  onChange: (value: NullableBoolean) => void;
}) {
  const labelId = useId();
  return (
    <div className="triState" role="group" aria-labelledby={labelId}>
      <span id={labelId}>{label}</span>
      <div>
        {OPTIONS.map((option) => (
          <button
            aria-pressed={value === option.value}
            className={value === option.value ? "active" : ""}
            key={option.label}
            type="button"
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
