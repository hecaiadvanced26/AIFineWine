import React from 'react';

export default function OrderConfirmation({ order }) {
  const total = new Intl.NumberFormat('en', { style: 'currency', currency: 'EUR' })
    .format(order.total_cents / 100);
  return <section className="confirmation" role="status" aria-label="Order confirmed">
    <span className="confirmation-check" aria-hidden="true">✓</span>
    <div className="confirmation-body">
      <span className="eyebrow">THANK YOU FOR YOUR ORDER</span>
      <h2>Order confirmed</h2>
      <p>Your order confirmation is ready.</p>
      <div className="confirmation-summary"><span>{order.quantity} × {order.name}</span>
        <strong>{total}</strong></div>
      <p className="confirmation-vintage">Vintage {order.vintage ?? 'not specified'}</p>
      <details><summary>Order details</summary><p>Reference: <code>{order.order_id}</code></p></details>
      <small>Saved to the demo shop. No payment taken, email sent or delivery scheduled.</small>
    </div>
  </section>;
}
