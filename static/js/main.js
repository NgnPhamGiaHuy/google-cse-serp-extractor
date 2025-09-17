'use strict';
(function () {
    const $ = (id) => document.getElementById(id);

    function updateSplitHint(q) {
        if (!q) { $('long-query-hint').style.display = 'none'; return }
        const n = Math.ceil(q.length / 80);
        $('long-query-hint').textContent = n > 1 ? `Will split into ${n} subqueries` : '';
        $('long-query-hint').style.display = n > 1 ? 'block' : 'none';
        $('split-count').textContent = n > 1 ? `${n} subqueries expected` : '';
    }
    window.updateSplitHint = updateSplitHint;

    document.addEventListener('DOMContentLoaded', function () {
        window.state = window.state || { file: null, parsed: null, jobId: null, results: [], page: 1, perPage: 100 };
        window.usageInterval = window.usageInterval || null;

        if (window.checkTokenStatus) window.checkTokenStatus();
        if (window.refreshUsage) window.refreshUsage();

        if (window.initializePlatformInput) window.initializePlatformInput();
        if (window.initializeModeToggle) window.initializeModeToggle();
        if (window.initializeFileUpload) window.initializeFileUpload();
        if (window.initializeResultsControls) window.initializeResultsControls();

        document.getElementById('manual-query').addEventListener('input', (e) => window.updateSplitHint(e.target.value));

        $('google-api-key').addEventListener('input', window.updateTokenStatus);
        $('google-cx').addEventListener('input', window.updateTokenStatus);
        $('save-tokens').addEventListener('click', window.saveTokens);
        $('validate-tokens').addEventListener('click', window.validateTokens);
        $('clear-tokens').addEventListener('click', window.clearTokens);

        $('save-backup-tokens').addEventListener('click', window.saveBackupTokens);
        $('validate-backup-tokens').addEventListener('click', window.validateBackupTokens);
        $('clear-backup-tokens').addEventListener('click', window.clearBackupTokens);

        // removed run-single button handler; use Start batch instead

        $('start-batch').addEventListener('click', () => {
            if (window.state.parsed?.keywords?.length) { window.startJob(window.state.parsed.keywords); }
            else {
                const queryText = $('manual-query').value.trim();
                if (queryText) {
                    try {
                        const jsonData = JSON.parse(queryText);
                        if (jsonData.keywords && Array.isArray(jsonData.keywords)) { window.startJob(jsonData.keywords); return; }
                    } catch (e) { }
                    const queries = queryText.split('\n').filter(q => q.trim()).map(q => q.trim());
                    if (queries.length > 0) { window.startJob(queries); return; }
                }
                const startHelper = document.getElementById('start-helper');
                if (startHelper) { startHelper.textContent = 'Add a file or enter a query to start.'; }
                const queryArea = document.getElementById('manual-query');
                if (queryArea) { queryArea.setAttribute('aria-invalid', 'true'); }
                setTimeout(() => { if (queryArea) queryArea.removeAttribute('aria-invalid'); }, 2000);
            }
        });

        $('clear').addEventListener('click', () => {
            window.state.file = null;
            window.state.parsed = null;
            window.state.jobId = null;
            window.state.results = [];
            window.state.page = 1;
            window.state.startTime = null;
            if (window.usageInterval) { clearInterval(window.usageInterval); window.usageInterval = null; }
            $('file-input').value = '';
            $('file-preview').style.display = 'none';
            $('preview-table').innerHTML = '';
            $('validation-errors').textContent = '';
            $('manual-query').value = '';
            if (window.hideProgressBar) window.hideProgressBar();
            $('results-list').innerHTML = '';
            $('filter-query').value = '';
            $('page-indicator').textContent = 'Page 1';
            $('results-section').style.display = 'none';
        });

        if (window.__enableQuotaAwarePoll) window.__enableQuotaAwarePoll();

        // Accessible tooltip toggling: maintain aria-expanded on trigger and aria-hidden on tooltip
        const tooltipTriggers = document.querySelectorAll('.tooltip-trigger[aria-describedby]');
        tooltipTriggers.forEach((btn) => {
            const tipId = btn.getAttribute('aria-describedby');
            const tip = tipId ? document.getElementById(tipId) : null;
            if (!tip) return;
            function showTip() { btn.setAttribute('aria-expanded', 'true'); tip.setAttribute('aria-hidden', 'false'); }
            function hideTip() { btn.setAttribute('aria-expanded', 'false'); tip.setAttribute('aria-hidden', 'true'); }
            btn.addEventListener('click', (e) => { e.preventDefault(); const expanded = btn.getAttribute('aria-expanded') === 'true'; if (expanded) hideTip(); else showTip(); });
            btn.addEventListener('keydown', (e) => { if (e.key === 'Escape') hideTip(); });
            // Hide when clicking outside
            document.addEventListener('click', (e) => { if (!btn.contains(e.target) && !tip.contains(e.target)) hideTip(); });
            // Initialize state
            hideTip();
        });
    });
})();
