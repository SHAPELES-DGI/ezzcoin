/* © 2026 Ezzcoins. All rights reserved. Copying or reuse of this code is not permitted. */
// The contact form on /contact/. Messages go to Ezzcoins' Firestore "reports" collection, the same one the
// player pages' "report a problem" link uses (kind "other", page "/contact/"); its rules only allow creating
// a report, so visitors can't read, change or delete any message.
(() => {
  'use strict';
  const form = document.getElementById('contact-form');
  if (!form) return;
  const endpoint = 'https://firestore.googleapis.com/v1/projects/ezzcoin-d5316/databases/(default)/documents/reports?key=AIzaSyDV6oQlHWc1mFCeo-ywnjy47nbq1lNvCD8';
  const msg = form.querySelector('.msg'), send = form.querySelector('button[type=submit]'), text = form.querySelector('textarea');
  const count = form.querySelector('[data-count]');
  const say = (t, bad) => { msg.textContent = t; msg.className = 'msg' + (bad ? ' bad' : ''); };
  const left = () => { if (count) count.textContent = `${Math.max(0, 400 - text.value.length)} characters left`; };
  text.addEventListener('input', left); left();
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const data = new FormData(form);
    const body = String(data.get('message') || '').trim();
    const email = String(data.get('email') || '').trim();
    if (body.length < 5) { say('Please write a short message first.', true); text.focus(); return; }
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { say('That email address doesn’t look right. Leave it empty if you don’t need a reply.', true); return; }
    let last = 0; try { last = Number(localStorage.getItem('ezzContact')) || 0; } catch {}
    if (Date.now() - last < 10 * 60000) { say('Thanks, your message is already in. You can send another in a few minutes.'); return; }
    const topic = ['Question', 'Correction', 'Idea', 'Business', 'Other'].includes(data.get('topic')) ? data.get('topic') : 'Other';
    const note = (`[${topic}] ${body.slice(0, 400)}` + (email ? `\nReply to: ${email}` : '')).slice(0, 500);
    send.disabled = true; say('Sending…');
    try {
      const r = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: { kind: { stringValue: 'other' }, note: { stringValue: note }, page: { stringValue: '/contact/' } } }),
        signal: AbortSignal.timeout(15000) });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      try { localStorage.setItem('ezzContact', String(Date.now())); } catch {}
      form.reset(); left(); say('Thanks! Your message was sent.' + (email ? ' We’ll reply by email.' : ''));
    } catch { say('Couldn’t send it right now. Please try again in a minute.', true); }
    finally { send.disabled = false; }
  });
})();
