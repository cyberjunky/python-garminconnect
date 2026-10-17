"use client";

type Props = {
  models?: string[];
  value?: string;
  onChange?: (model: string) => void;
  disabled?: boolean;
};

export function CoachModelSelect(_props: Props = {}) {
  return (
    <div className="coach-model-select coach-model-static" aria-label="Modelo exclusivo">
      <span className="coach-model-icon" aria-hidden="true">✦</span>
      <span className="coach-model-badge">GPT-6 Luna · High</span>
    </div>
  );
}
