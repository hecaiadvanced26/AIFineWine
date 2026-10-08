import React, { useEffect, useRef, useState } from 'react';
import Markdown from 'react-markdown';
import { post, streamChat } from './api.js';
import OrderCard from './OrderCard.jsx';
import OrderConfirmation from './OrderConfirmation.jsx';
import { Comparison, QuickReplies, Recommendations } from './Advisor.jsx';

const CONTACT_EMAIL = 'cave@hec.edu'; // fictional demo address; keep in sync with prompts.py
const suggestions = ['Help me choose a wine', 'A red wine under €12', 'Find a cheaper alternative to a wine I like'];

function Glass() {
  return <svg viewBox="0 0 80 100" fill="none" aria-hidden="true">
    <path d="M24 12h32l4 26c2 15-7 26-20 26S18 53 20 38l4-26ZM40 64v24M26 89h28" />
    <path className="wine-fill" d="M22 37h36c2 14-5 24-18 24S20 51 22 37Z" />
  </svg>;
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(true);
  const [status, setStatus] = useState('Loading conversation…');
  const [events, setEvents] = useState([]);
  const [error, setError] = useState('');
  const [draft, setDraft] = useState(null);
  const end = useRef(null);
  const running = useRef(true);
  useEffect(() => {
    post('/api/reset').then(() => setStatus('You are connected to Dave from HEC Cave. Please let me know how to help you'))
      .catch(failure => { setError(failure.message); setStatus('Connection failed'); })
      .finally(() => { running.current = false; setBusy(false); });
  }, []);
  useEffect(() => { end.current?.scrollIntoView({ block: 'end' }); }, [messages, draft]);

  function replaceReply(content, extras = {}) {
    setMessages(previous => [...previous.slice(0, -1), { role: 'assistant', content, ...extras }]);
  }

  async function send(text) {
    text = text.trim();
    if (!text || running.current) return;
    running.current = true;
    setBusy(true); setError(''); setInput(''); setDraft(null); setEvents([]);
    setStatus('Sending your message…');
    setMessages(previous => [...previous, { role: 'user', content: text },
      { role: 'assistant', content: '' }]);
    let reply = '';
    try {
      await streamChat(text, event => {
        if (event.type === 'status') {
          setStatus(event.text); setEvents(previous => [...previous, event.text]);
        } else if (event.type === 'text') {
          reply += event.text; replaceReply(reply);
        } else if (event.type === 'done') {
          replaceReply(event.reply, { recommendations: event.recommendations,
            comparison: event.comparison, choices: event.choices });
          setDraft(event.draft);
        }
      });
    } catch (failure) {
      setError(failure.message); setStatus('Request failed');
      replaceReply('Reply unavailable or interrupted. Please try again.');
    } finally { running.current = false; setBusy(false); }
  }

  async function orderAction(action) {
    if (running.current) return;
    running.current = true; setBusy(true); setError('');
    setStatus(action === 'confirm' ? 'Rechecking stock and exporting order…' : 'Cancelling draft…');
    try {
      const result = await post('/api/order', { action, order_id: draft.order_id });
      setDraft(result.draft); setStatus(action === 'confirm' ? 'Order request complete' : 'Draft cancelled');
      setMessages(previous => [...previous, { role: 'assistant', content: result.reply,
        confirmation: result.confirmation }]);
    } catch (failure) {
      setError(failure.message); setStatus('Order action failed');
      if (failure.draft !== undefined) setDraft(failure.draft);
    } finally { running.current = false; setBusy(false); }
  }

  async function changeQuantity(quantity) {
    if (running.current || !draft) return;
    running.current = true; setBusy(true); setError(''); setStatus('Checking stock for the new quantity…');
    try {
      const result = await post('/api/order', { action: 'quantity', order_id: draft.order_id, quantity });
      setDraft(result.draft); setStatus('Draft updated');
    } catch (failure) {
      setError(failure.message); setStatus('Quantity not changed');
      if (failure.draft !== undefined) setDraft(failure.draft);
    } finally { running.current = false; setBusy(false); }
  }

  async function reset() {
    if (running.current) return;
    running.current = true; setBusy(true); setStatus('Starting new conversation…');
    try {
      await post('/api/reset');
      setMessages([]); setDraft(null); setError(''); setEvents([]); setStatus('Ready when you are');
    } catch (failure) { setError(failure.message); setStatus('Could not reset conversation'); }
    finally { running.current = false; setBusy(false); }
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <a href="/" className="brand" aria-label="HEC Cave home">HEC Cave<span>WINE, LIKE AN EXPERT</span></a>
      <button className="new-chat" onClick={reset} disabled={busy}>＋ New conversation</button>
      <div className="sidebar-note"><span className="eyebrow">A LITTLE GUIDANCE</span>
        <h2>Your perfect bottle.<br />A simple conversation.</h2>
        <p>Tell us your taste, preferred origin or budget. We’ll find a match in our caves catalog.</p>
        <ul><li>Expert ratings</li><li>Live availability checks</li><li>1-click purchase</li><li>Find better alternatives</li></ul>
      </div>
      <p className="demo-note">COURSE DEMO BY GROUP 3<br />Real wines · Illustrative shop data<br />Rayen G., Jan L.<br />Mariia T., Selin Z.</p>
    </aside>
    <main className="chat-shell">
      <header className="topbar"><div><span className="eyebrow">DAVE</span>
        <p>Let’s find your next bottle.</p></div><div className="topbar-actions">
          <a className="contact-btn" href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent('Question for the HEC Cave team')}`}>
            <span aria-hidden="true">Contact</span> Customer contact</a>
          <span className="tag">Demo catalog</span></div></header>
      <div className="conversation">
        {!messages.length && <section className="welcome"><div className="glass"><Glass /></div>
          <span className="eyebrow"></span><h1>Your wine, found.</h1>
          <p>Start with what matters to you.</p>
          <div className="suggestions">{suggestions.map(text => <button key={text}
            disabled={busy} onClick={() => send(text)}>{text} <span>↗</span></button>)}</div>
        </section>}
        {messages.map((message, index) => message.confirmation
          ? <OrderConfirmation key={index} order={message.confirmation} />
          : <React.Fragment key={index}><article className={`message ${message.role}`}>
          <div className="avatar" aria-hidden="true">{message.role === 'user' ? 'Y' : 'D'}</div>
          <div className="message-body"><span className="speaker">{message.role === 'user' ? 'You' : 'Dave'}</span>
            {message.content ? <Markdown>{message.content}</Markdown> : <p className="waiting">I am working on your request…</p>}
          </div></article>
          <Recommendations data={message.recommendations} onAsk={send} disabled={busy} />
          <Comparison data={message.comparison} onAsk={send} disabled={busy} />
          {index === messages.length - 1 && !busy &&
            <QuickReplies data={message.choices} onPick={send} disabled={busy} />}
          </React.Fragment>)}
        <OrderCard draft={draft} busy={busy} onAction={orderAction} onQuantity={changeQuantity} /><div ref={end} />
      </div>
      <div className="composer-area">
        <div className="activity" role="status" aria-live="polite">
          <span className={`status-dot ${busy ? 'active' : ''}`} />{status}
        </div>
        {events.length > 0 && <details className="activity-log"><summary>View activity</summary>
          <ol>{events.map((event, index) => <li key={index}>{event}</li>)}</ol></details>}
        {error && <p className="error" role="alert">{error}</p>}
        <form className="composer" onSubmit={event => { event.preventDefault(); send(input); }}>
          <label className="sr-only" htmlFor="message">Your message</label>
          <textarea id="message" rows="2" value={input} disabled={busy} maxLength={4000}
            placeholder="Tell us your taste, preferred origin or budget…" onChange={event => setInput(event.target.value)}
            onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault(); send(input);
            } }} />
          <button className="send" aria-label="Send message" disabled={busy || !input.trim()}>↑</button>
        </form>
        <p className="composer-note">Wines & ratings from Vivino. Bottle pictures are illustrations. Demo prices & inventory; no payments taken.</p>
      </div>
    </main>
  </div>;
}
