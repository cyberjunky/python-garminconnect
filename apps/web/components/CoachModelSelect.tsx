"use client";

import { savePreferredModel } from "@/lib/openaiModels";

type Props = {
  models: string[];
  value: string;
  onChange: (model: string) => void;
  disabled?: boolean;
};

export function CoachModelSelect({ models, value, onChange, disabled }: Props) {
  if (models.length === 0) return null;

  return (
    <label className="coach-model-select">
      <span className="coach-model-icon" aria-hidden>✦</span>
      <select
        value={value}
        disabled={disabled}
        onChange={(event) => {
          const next = event.target.value;
          savePreferredModel(next);
          onChange(next);
        }}
        aria-label="Modelo de OpenAI"
      >
        {models.map((model) => (
          <option key={model} value={model}>
            {model}
          </option>
        ))}
      </select>
    </label>
  );
}
