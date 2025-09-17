'use strict';
(function () {
    window.applyQueryTransformation = function applyQueryTransformation(query) {
        if (!query || !query.trim()) { return query; }
        const siteFilters = Array.from((window.selectedPlatforms || new Map()).values()).map(platform => platform.siteFilter);
        if (siteFilters.length === 0) { return query; }
        const queryLower = query.toLowerCase();
        const hasExistingSiteFilter = siteFilters.some(site => { const domain = site.split(':')[1]; return domain && queryLower.includes(domain); });
        if (hasExistingSiteFilter) { return query; }
        return `${query} (${siteFilters.join(' OR ')})`;
    }

    window.generateQueryPreview = function generateQueryPreview() {
        const queryPreview = document.getElementById('query-preview');
        const queryPreviewText = document.getElementById('query-preview-text');
        const queryMode = document.getElementById('query-mode');
        if (queryMode.style.display === 'none') { queryPreview.style.display = 'none'; return; }
        if ((window.selectedPlatforms && window.selectedPlatforms.size === 0) || !window.selectedPlatforms) { queryPreview.style.display = 'none'; return; }
        queryPreview.style.display = 'block';
        const manualQuery = document.getElementById('manual-query').value.trim();
        if (!manualQuery) { queryPreviewText.textContent = 'Enter a search query to see preview...'; return; }
        try {
            const jsonData = JSON.parse(manualQuery);
            if (jsonData.keywords && Array.isArray(jsonData.keywords)) {
                const transformedKeywords = jsonData.keywords.map(keyword => window.applyQueryTransformation(keyword));
                queryPreviewText.textContent = `JSON Keywords (${transformedKeywords.length}):\n\n${transformedKeywords.join('\n')}`;
                return;
            }
        } catch (e) { }
        const queries = manualQuery.split('\n').filter(q => q.trim()).map(q => q.trim());
        if (queries.length > 1) {
            const transformedQueries = queries.map(query => window.applyQueryTransformation(query));
            queryPreviewText.textContent = `Multiple Queries (${transformedQueries.length}):\n\n${transformedQueries.join('\n')}`;
        } else {
            const transformedQuery = window.applyQueryTransformation(queries[0]);
            queryPreviewText.textContent = transformedQuery;
        }
    }

    window.updateFilePreview = function updateFilePreview() {
        const fileMode = document.getElementById('file-mode');
        const filePreview = document.getElementById('file-preview');
        if (fileMode.style.display === 'none') { filePreview.style.display = 'none'; return; }
        if (!window.state || !state.parsed || !state.parsed.keywords) { filePreview.style.display = 'none'; return; }
        filePreview.style.display = 'block';
        const rows = state.parsed.keywords.slice(0, 5);
        const table = document.createElement('table');
        table.style.width = '100%';
        table.style.borderCollapse = 'collapse';
        table.innerHTML = '<thead><tr><th style="text-align:left;padding:6px;border-bottom:1px solid var(--border)">keyword</th></tr></thead>';
        const tb = document.createElement('tbody');
        rows.forEach(keyword => {
            const tr = document.createElement('tr');
            const transformedKeyword = window.applyQueryTransformation(keyword);
            tr.innerHTML = `<td style="padding:6px;border-bottom:1px solid var(--border)">${transformedKeyword}</td>`;
            tb.appendChild(tr);
        });
        table.appendChild(tb);
        document.getElementById('preview-table').innerHTML = '';
        document.getElementById('preview-table').appendChild(table);
    }

    window.updateAllPreviews = function updateAllPreviews() {
        window.generateQueryPreview();
        window.updateFilePreview();
    }

    window.copyQueryToClipboard = async function copyQueryToClipboard() {
        const queryPreviewText = document.getElementById('query-preview-text');
        const query = queryPreviewText.textContent;
        try {
            await navigator.clipboard.writeText(query);
            const copyBtn = document.getElementById('copy-query-btn');
            const originalTitle = copyBtn.title;
            copyBtn.title = 'Copied!';
            copyBtn.style.color = 'var(--accent)';
            setTimeout(() => { copyBtn.title = originalTitle; copyBtn.style.color = ''; }, 2000);
        } catch (err) {
            console.warn('Failed to copy query:', err);
            const textArea = document.createElement('textarea');
            textArea.value = query;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
        }
    }
})();
