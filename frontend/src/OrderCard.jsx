import React from 'react';

export default function OrderCard({ draft, busy, onAction }) {
  if (!draft) return null;
  const euros = new Intl.NumberFormat('en', { style: 'currency', currency: 'EUR' });
  return <section className="order-card" aria-labelledby="order-title">
    <div className="order-heading"><span className="eyebrow">YOUR SELECTION</span>
      <span className="tag">Awaiting confirmation</span></div>
    <h2 id="order-title">{draft.name}</h2>
    <p>{draft.wine_id} · Vintage {draft.vintage ?? 'not specified'}</p>
    <div className="order-total"><span>{draft.quantity} bottles</span>
      <strong>{euros.format(draft.total_cents / 100)}</strong></div>
    <div className="order-actions">
      <button className="primary" disabled={busy} onClick={() => onAction('confirm')}>Confirm order</button>
      <button className="secondary" disabled={busy} onClick={() => onAction('cancel')}>Cancel</button>
    </div>
    <small>Local demo export only. No payment. A new message replaces this draft.</small>
  </section>;
}
