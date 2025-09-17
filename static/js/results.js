'use strict';
(function () {
    const $ = (id) => document.getElementById(id);
    const isMobile = (typeof window !== 'undefined' && window.matchMedia) ? window.matchMedia('(max-width: 600px)').matches : false;

    window.loadResults = async function loadResults() {
        // show skeletons while fetching
        const list = $('results-list');
        if (list) {
            list.setAttribute('aria-busy', 'true');
            list.innerHTML = '';
            for (let i = 0; i < 8; i++) {
                const sk = document.createElement('div'); sk.className = 'result-card skeleton-card'; list.appendChild(sk);
            }
        }
        const res = await fetch(`/api/job-results/${window.state.jobId}`);
        if (!res.ok) return;
        const data = await res.json();
        window.state.results = Array.isArray(data.results) ? data.results : [];
        window.setExportsEnabled(window.state.results.length > 0);
        if (window.state.results.length > 0) { $('results-section').style.display = 'block'; }
        window.renderResults();
        if (list) { list.setAttribute('aria-busy', 'false'); }
    }

    window.renderResults = function renderResults() {
        const q = ($('filter-query').value || '').toLowerCase();
        const flattened = window.flattenOrganic(window.state.results);
        const filtered = flattened.filter(entry => window.entryMatchesQuery(entry, q));
        const start = (window.state.page - 1) * window.state.perPage; const end = start + window.state.perPage;
        const pageItems = filtered.slice(start, end);
        const list = $('results-list'); list.innerHTML = '';
        if (pageItems.length === 0) {
            const empty = document.createElement('div'); empty.className = 'muted';
            empty.textContent = flattened.length === 0 ? 'No results yet.' : 'No results match the filter.';
            list.appendChild(empty);
        }
        const frag = document.createDocumentFragment();
        pageItems.forEach(({ item, result }) => {
            const el = document.createElement('div'); el.className = 'result-card';
            const sq = item.searchQuery || {};
            const term = sq.term || '';
            const page = sq.page || item.page || 1;
            const device = '';
            const country = '';
            const language = '';
            const title = result.title || '';
            const url = result.url || result.link || '';
            const desc = result.description || result.snippet || '';
            const pos = result.position || '';
            el.innerHTML = `
                    <div class="result-rank muted">#${pos} · organic</div>
                    <h3 class="result-title"><a href="${window.escapeAttr(url)}" target="_blank" rel="noopener noreferrer">${window.escapeHtml(title || url)}</a></h3>
                    <div class="result-url">${window.escapeHtml(url)}</div>
                    <div class="result-snippet">${window.escapeHtml(desc)}</div>
                    <div class="result-meta">${window.escapeHtml(term)} · page ${page}</div>
                `;
            frag.appendChild(el);
        });
        list.appendChild(frag);
        const totalPages = Math.max(1, Math.ceil(filtered.length / window.state.perPage));
        $('page-indicator').textContent = `Page ${window.state.page} / ${totalPages}`;
    }

    window.flattenOrganic = function flattenOrganic(items) {
        const out = [];
        for (const item of items || []) {
            const organic = Array.isArray(item.organicResults) ? item.organicResults : [];
            for (const result of organic) out.push({ item, result });
        }
        return out;
    }

    window.entryMatchesQuery = function entryMatchesQuery(entry, q) {
        if (!q) return true;
        try {
            const item = entry.item || {};
            const result = entry.result || {};
            const term = String((item.searchQuery && item.searchQuery.term) || '').toLowerCase();
            const title = String(result.title || '').toLowerCase();
            const url = String(result.url || result.link || '').toLowerCase();
            return term.includes(q) || title.includes(q) || url.includes(q);
        } catch (_) { return false; }
    }

    window.escapeHtml = function escapeHtml(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    window.escapeAttr = function escapeAttr(s) {
        return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    window.exportFormat = async function exportFormat(fmt) {
        if (!window.state.jobId) { alert('No job yet'); return; }
        const btnMap = { json: 'export-json', csv: 'export-csv', xlsx: 'export-xlsx' };
        const btn = $(btnMap[fmt]);
        if (btn) { btn.setAttribute('data-loading', 'true'); btn.dataset.originalText = btn.textContent; btn.textContent = 'Exporting…'; btn.disabled = true; }
        const form = new FormData(); form.append('format', fmt);
        const res = await fetch(`/api/export-results/${window.state.jobId}`, { method: 'POST', body: form });
        const data = await res.json(); if (!res.ok || !data.success) {
            if (btn) { btn.setAttribute('data-status', 'error'); btn.textContent = 'Export failed'; setTimeout(() => { btn.removeAttribute('data-status'); btn.removeAttribute('data-loading'); btn.textContent = btn.dataset.originalText || 'Export'; btn.disabled = false; }, 1000); }
            alert(data.detail || 'Export failed'); return;
        }
        const a = document.createElement('a'); a.href = data.download_url; a.download = data.filename; document.body.appendChild(a); a.click(); a.remove();
        if (btn) { btn.setAttribute('data-status', 'success'); btn.textContent = 'Downloaded'; setTimeout(() => { btn.removeAttribute('data-status'); btn.removeAttribute('data-loading'); btn.textContent = btn.dataset.originalText || btn.textContent; btn.disabled = false; }, 900); }
    }

    window.setExportsEnabled = function setExportsEnabled(enabled) {
        ['export-json', 'export-csv', 'export-xlsx'].forEach(id => { const btn = $(id); btn.disabled = !enabled; btn.style.opacity = enabled ? '1' : '0.6'; });
    }

    window.initializeResultsControls = function initializeResultsControls() {
        function debounce(fn, ms = 200) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
        $('filter-query').addEventListener('input', debounce(() => { window.state.page = 1; window.renderResults(); }, 200));
        $('prev-page').addEventListener('click', () => { window.state.page = Math.max(1, window.state.page - 1); window.renderResults(); });
        $('next-page').addEventListener('click', () => { const q = ($('filter-query').value || '').toLowerCase(); const flattened = window.flattenOrganic(window.state.results); const filtered = flattened.filter(entry => window.entryMatchesQuery(entry, q)); const totalPages = Math.max(1, Math.ceil(filtered.length / window.state.perPage)); window.state.page = Math.min(totalPages, window.state.page + 1); window.renderResults(); });
        $('export-json').addEventListener('click', () => window.exportFormat('json'));
        $('export-csv').addEventListener('click', () => window.exportFormat('csv'));
        $('export-xlsx').addEventListener('click', () => window.exportFormat('xlsx'));
        window.setExportsEnabled(false);
    }
})();
