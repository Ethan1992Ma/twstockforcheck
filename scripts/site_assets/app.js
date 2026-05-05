/* TW Coverage — client-side search */
(function () {
  'use strict';

  const BASE = window.SITE_BASE || '';
  let index = null;

  function esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  async function loadIndex() {
    if (index) return index;
    try {
      const res = await fetch(`${BASE}/search-index.json`);
      index = await res.json();
    } catch (_) {
      index = [];
    }
    return index;
  }

  function search(query, limit) {
    limit = limit || 8;
    if (!index || !query.trim()) return [];
    const q = query.toLowerCase();
    const results = [];

    for (const item of index) {
      let score = 0;
      if (item.t === q || item.t.startsWith(q))  score += 10;
      if (item.n.toLowerCase().includes(q))        score += 8;
      if (item.s.toLowerCase().includes(q))        score += 3;
      for (const w of item.w) {
        if (w.toLowerCase().includes(q)) { score += 4; break; }
      }
      if (score > 0) results.push({ item, score });
    }

    return results
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map(r => r.item);
  }

  function renderDropdown(results, container) {
    if (!results.length) { container.textContent = ''; return; }
    // Build DOM nodes — no raw user HTML, ticker/name/sector are our own data
    container.textContent = '';
    results.forEach(r => {
      const a = document.createElement('a');
      a.className = 'sr-item';
      a.href = `${BASE}/ticker/${esc(r.t)}.html`;

      const ticker = document.createElement('span');
      ticker.className = 'sr-ticker';
      ticker.textContent = r.t;

      const name = document.createElement('span');
      name.className = 'sr-name';
      name.textContent = r.n;

      const sector = document.createElement('small');
      sector.textContent = r.s;

      a.appendChild(ticker);
      a.appendChild(name);
      a.appendChild(sector);
      container.appendChild(a);
    });
  }

  function wire(inputId, dropdownId) {
    const input = document.getElementById(inputId);
    const drop  = document.getElementById(dropdownId);
    if (!input || !drop) return;

    input.addEventListener('focus', loadIndex);

    input.addEventListener('input', async () => {
      await loadIndex();
      renderDropdown(search(input.value), drop);
    });

    input.addEventListener('keydown', e => {
      if (e.key === 'Escape') { drop.textContent = ''; input.blur(); }
    });

    document.addEventListener('click', e => {
      if (!input.contains(e.target) && !drop.contains(e.target)) {
        drop.textContent = '';
      }
    });
  }

  wire('nav-search',  'nav-results');
  wire('hero-search', 'hero-results');
})();
