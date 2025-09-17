'use strict';
(function () {
    window.initializeModeToggle = function initializeModeToggle() {
        const fileModeBtn = document.getElementById('file-mode-btn');
        const queryModeBtn = document.getElementById('query-mode-btn');
        const fileMode = document.getElementById('file-mode');
        const queryMode = document.getElementById('query-mode');
        let currentMode = 'file';
        function switchMode(mode) {
            fileModeBtn.classList.toggle('active', mode === 'file');
            queryModeBtn.classList.toggle('active', mode === 'query');
            fileMode.style.display = mode === 'file' ? 'block' : 'none';
            queryMode.style.display = mode === 'query' ? 'block' : 'none';
            // ARIA states for tabs
            fileModeBtn.setAttribute('aria-selected', String(mode === 'file'));
            queryModeBtn.setAttribute('aria-selected', String(mode === 'query'));
            fileModeBtn.setAttribute('aria-pressed', String(mode === 'file'));
            queryModeBtn.setAttribute('aria-pressed', String(mode === 'query'));
            fileMode.setAttribute('aria-hidden', String(mode !== 'file'));
            queryMode.setAttribute('aria-hidden', String(mode !== 'query'));
            currentMode = mode;
            if (window.updateAllPreviews) window.updateAllPreviews();
            // Move focus to first control in active panel
            const firstFocusable = (mode === 'file') ? document.getElementById('file-input') : document.getElementById('manual-query');
            if (firstFocusable) firstFocusable.focus();
        }
        fileModeBtn.addEventListener('click', () => switchMode('file'));
        queryModeBtn.addEventListener('click', () => switchMode('query'));
        // Optional: arrow key navigation between tabs
        function onTabKeydown(e) {
            const key = e.key;
            if (key !== 'ArrowLeft' && key !== 'ArrowRight') return;
            e.preventDefault();
            if (key === 'ArrowLeft') { switchMode(currentMode === 'file' ? 'query' : 'file'); (currentMode === 'file' ? fileModeBtn : queryModeBtn).focus(); }
            else if (key === 'ArrowRight') { switchMode(currentMode === 'file' ? 'query' : 'file'); (currentMode === 'file' ? fileModeBtn : queryModeBtn).focus(); }
        }
        fileModeBtn.addEventListener('keydown', onTabKeydown);
        queryModeBtn.addEventListener('keydown', onTabKeydown);
        switchMode('file');
    }
})();
