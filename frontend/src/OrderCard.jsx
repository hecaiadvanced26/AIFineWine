import React from 'react';
import Stepper from './Stepper.jsx';

export default function OrderCard({ draft, busy, onAction, onQuantity }) {
  if (!draft) return null;
  const euros = new Intl.NumberFormat('en', { style: 'currency', currency: 'EUR' });
  return <section className="order-card" aria-labelledby="order-title">
    <div className="order-heading"><span className="eyebrow">YOUR SELECTION</span>
      <span className="tag">Awaiting confirmation</span></div>
    <h2 id="order-title">{draft.name}</h2>
    <p>{draft.wine_id} · Vintage {draft.vintage ?? 'not specified'}</p>
    <div className="order-total"><span className="qty-line">
      {onQuantity && draft.max_quantity > 1
        ? <Stepper value={draft.quantity} max={draft.max_quantity} disabled={busy} onChange={onQuantity} label="Bottles" />
        : <span>{draft.quantity} {draft.quantity === 1 ? 'bottle' : 'bottles'}</span>}
      {draft.max_quantity != null && <small className="qty-max">{draft.max_quantity} in stock</small>}</span>
      <strong>{euros.format(draft.total_cents / 100)}</strong></div>
    <div className="order-actions">
      <button className="primary" disabled={busy} onClick={() => onAction('confirm')}>Confirm order</button>
      <button className="secondary" disabled={busy} onClick={() => onAction('cancel')}>Cancel</button>
    </div>
    <small>Local demo export only. No payment. A new message replaces this draft.</small>
  </section>;
}
