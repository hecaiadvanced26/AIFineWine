import React from 'react';

const euros = new Intl.NumberFormat('en', { style: 'currency', currency: 'EUR' });
const FAMILY = { 'Red-wine fruit': 'red fruit', 'White-wine fruit': 'citrus & orchard fruit',
  'Floral': 'flowers', 'Oak ageing': 'spice, vanilla & toast', 'Vegetal': 'herbs & green notes', 'Mineral': 'mineral notes' };
const friendly = text => Object.entries(FAMILY).reduce((out, [key, value]) => out.replace(key, value),
  text.replace('aroma family:', 'aroma:').replace('taster-stated', 'the taster wrote it')
    .replace('style guess', 'typical for the style, not tasted'));

function Glass({ filled }) {
  return <svg viewBox="0 0 80 100" className={`glass-icon ${filled ? 'on' : ''}`} aria-hidden="true">
    <path d="M24 12h32l4 26c2 15-7 26-20 26S18 53 20 38l4-26ZM40 64v24M26 89h28" />
    <path className="fill" d="M22 37h36c2 14-5 24-18 24S20 51 22 37Z" />
  </svg>;
}

export function FitGlasses({ score }) {
  if (!score) return null;
  return <div className="fit-glasses" role="img" aria-label={`Fit with your wishes: ${score} out of 5 glasses`}>
    {[1, 2, 3, 4, 5].map(n => <Glass key={n} filled={n <= score} />)}
    <span>{score}/5 fit</span>
  </div>;
}

export function Stars({ value }) {
  if (value == null) return <span className="stars-none">No community rating</span>;
  return <span className="stars-row" role="img" aria-label={`Community rating ${value} out of 5`}>
    <span className="stars" style={{ '--pct': `${Math.max(0, Math.min(5, value)) / 5 * 100}%` }} aria-hidden="true">★★★★★</span>
    <span>{value}/5</span></span>;
}

function WineCard({ wine, onAsk, disabled, badge, plain }) {
  const place = [wine.country, wine.region].filter(Boolean).join(' · ');
  return <article className="wine-card">
    {badge && <span className="wine-badge">{badge}</span>}
    <h3>{wine.name}</h3>
    <div className="wine-meta">
      {wine.wine_type && <span>{wine.wine_type}</span>}
      {place && <span>{place}</span>}
      <span>{wine.vintage ? `Vintage ${wine.vintage}` : 'Vintage unknown'}</span>
    </div>
    {!plain && <FitGlasses score={wine.fit_score} />}
    <div className="wine-price">{euros.format(wine.price_eur)} <small>demo price · {wine.stock} in stock</small></div>
    {!plain && wine.wishes_total > 0 && <>
      <p className="wine-fit">Fits {wine.wishes_met} of {wine.wishes_total} of your wishes</p>
      <ul className="wine-wishes">
        {wine.matched.map(item => <li key={item} className="yes"><span aria-hidden="true">✓</span> {friendly(item)}</li>)}
        {wine.not_matched.map(item => <li key={item} className="no"><span aria-hidden="true">✕</span> Not met: {item}</li>)}
      </ul></>}
    {wine.shared_aromas?.length > 0 && <p className="wine-aromas">
      <strong>Shares with your choice:</strong> {wine.shared_aromas.join(', ')}</p>}
    {wine.aromas_stated.length > 0 && <p className="wine-aromas">
      <strong>The taster wrote:</strong> {wine.aromas_stated.join(', ')}</p>}
    {wine.aromas_style_guess.length > 0 && <p className="wine-aromas guess">
      <strong>Typical for this style (not tasted):</strong> {wine.aromas_style_guess.join(', ')}</p>}
    <p className="wine-ratings"><Stars value={wine.community_rating} />
      <span>Taster: {wine.taster_rating != null ? `${wine.taster_rating}/5` : 'no rating'}</span></p>
    {onAsk && <div className="wine-actions">
      <button className="primary" disabled={disabled}
        onClick={() => onAsk(`I'd like one bottle of ${wine.name} (${wine.wine_id}).`)}>Choose this wine</button>
      <button className="secondary" disabled={disabled}
        onClick={() => onAsk(`Is there a cheaper alternative to ${wine.name} (${wine.wine_id})?`)}>Cheaper alternative</button>
    </div>}
  </article>;
}

export function Recommendations({ data, onAsk, disabled }) {
  if (!data?.wines?.length) return null;
  return <section className="advisor-block" aria-label="Recommended wines">
    <span className="eyebrow">{data.wines.length === 1 ? 'ONE MATCH' : `${data.wines.length} MATCHES`}</span>
    <div className="wine-grid">
      {data.wines.map((wine, index) => <WineCard key={wine.wine_id} wine={wine} onAsk={onAsk} disabled={disabled}
        badge={index === 0 ? '#1 · Best fit' : `#${index + 1}`} />)}
    </div>
  </section>;
}

export function Comparison({ data, onAsk, disabled }) {
  if (!data?.alternatives?.length) return null;
  return <section className="advisor-block" aria-label="Comparison with cheaper alternatives">
    <span className="eyebrow">YOUR WINE VS. CHEAPER OPTIONS</span>
    <div className="wine-compare">
      <WineCard wine={data.chosen} plain badge="Your choice" />
      {data.alternatives.map(wine => <WineCard key={wine.wine_id} wine={wine} plain onAsk={onAsk}
        disabled={disabled} badge={`${euros.format(wine.price_difference_eur)} less`} />)}
    </div>
    <p className="wine-note">Similar means: same colour, lower price and shared aroma tags. It is not a tasting comparison.</p>
  </section>;
}

export function QuickReplies({ data, onPick, disabled }) {
  if (!data?.options?.length) return null;
  return <section className="advisor-block quick" aria-label="Quick answers">
    <div className="progress" role="progressbar" aria-valuemin="1" aria-valuemax={data.total}
      aria-valuenow={data.step} aria-label={`Question ${data.step} of ${data.total}`}>
      <span>Question {data.step} of {data.total}</span>
      <div className="progress-bar"><div style={{ width: `${(data.step / data.total) * 100}%` }} /></div>
    </div>
    <div className="choice-chips">
      {data.options.map(option => <button key={option} disabled={disabled} onClick={() => onPick(option)}>{option}</button>)}
    </div>
  </section>;
}
