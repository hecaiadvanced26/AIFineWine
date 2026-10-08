import React from 'react';

// Whole-number quantity selector limited to 1..max. The server re-checks stock on every change.
export default function Stepper({ value, max, onChange, disabled, label = 'Quantity' }) {
  const clamp = n => Math.max(1, Math.min(max, Math.floor(Number(n)) || 1));
  return <span className="stepper" role="group" aria-label={label}>
    <button type="button" disabled={disabled || value <= 1} aria-label="Fewer" onClick={() => onChange(clamp(value - 1))}>−</button>
    <input type="number" min="1" max={max} value={value} disabled={disabled} aria-label={label}
      onChange={event => onChange(clamp(event.target.value))} />
    <button type="button" disabled={disabled || value >= max} aria-label="More" onClick={() => onChange(clamp(value + 1))}>＋</button>
  </span>;
}
