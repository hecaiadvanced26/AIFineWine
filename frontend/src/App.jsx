import React, { useEffect, useRef, useState } from 'react';
import Markdown from 'react-markdown';
import { post, streamChat } from './api.js';
import OrderCard from './OrderCard.jsx';
import OrderConfirmation from './OrderConfirmation.jsx';

const suggestions = ['A red wine from Spain', 'White wines with stated citrus notes', 'Show wines under €20'];

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
    post('/api/reset').then(() => setStatus('Ready when you are'))
      .catch(failure => { setError(failure.message); setStatus('Connection failed'); })
      .finally(() => { running.current = false; setBusy(false); });
  }, []);
  useEffect(() => { end.current?.scrollIntoView({ block: 'end' }); }, [messages, draft]);

  function replaceReply(content) {
    setMessages(previous => [...previous.slice(0, -1), { role: 'assistant', content }]);
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
          replaceReply(event.reply); setDraft(event.draft);
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
      <a href="/" className="brand" aria-label="Cave home">cave<span>WINE, WITHOUT THE GUESSWORK</span></a>
      <button className="new-chat" onClick={reset} disabled={busy}>＋ New conversation</button>
      <div className="sidebar-note"><span className="eyebrow">A LITTLE GUIDANCE</span>
        <h2>A good bottle.<br />A simple conversation.</h2>
        <p>Tell us your taste, preferred origin or budget. We’ll find a match in the shop’s catalog.</p>
        <ul><li>Catalog-backed answers</li><li>Live availability checks</li><li>You confirm every order</li></ul>
      </div>
      <p className="demo-note">COURSE DEMO<br />Real wine names · Illustrative shop data</p>
    </aside>
    <main className="chat-shell">
      <header className="topbar"><div><span className="eyebrow">YOUR WINE ASSISTANT</span>
        <p>Let’s find your next bottle.</p></div><span className="tag">Demo catalog</span></header>
      <div className="conversation">
        {!messages.length && <section className="welcome"><div className="glass"><Glass /></div>
          <span className="eyebrow">PULL UP A CHAIR</span><h1>Your wine, found.</h1>
          <p>A bottle for tonight, a vintage you love, or something within budget.<br />Start with what matters to you.</p>
          <div className="suggestions">{suggestions.map(text => <button key={text}
            disabled={busy} onClick={() => send(text)}>{text} <span>↗</span></button>)}</div>
        </section>}
        {messages.map((message, index) => message.confirmation
          ? <OrderConfirmation key={index} order={message.confirmation} />
          : <article key={index} className={`message ${message.role}`}>
          <div className="avatar" aria-hidden="true">{message.role === 'user' ? 'Y' : 'c'}</div>
          <div className="message-body"><span className="speaker">{message.role === 'user' ? 'You' : 'Cave'}</span>
            {message.content ? <Markdown>{message.content}</Markdown> : <p className="waiting">Working on your request…</p>}
          </div></article>)}
        <OrderCard draft={draft} busy={busy} onAction={orderAction} /><div ref={end} />
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
        <p className="composer-note">Imported wines & ratings. Flavour notes distinguish stated and inferred. Demo prices & inventory; no payments taken.</p>
      </div>
    </main>
  </div>;
}
