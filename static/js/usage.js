'use strict';
(function () {
    window.refreshUsage = async function refreshUsage() {
        try {
            const res = await fetch('/api/usage');
            if (!res.ok) return;
            const data = await res.json();
            const usageText = document.getElementById('usage_text');
            if (usageText) usageText.textContent = `${data.used} / ${data.quota}`;
            const bar = document.getElementById('usage_bar');
            const fill = document.getElementById('usage_fill');
            const percent = Math.max(0, Math.min(100, Math.round((data.used / Math.max(1, data.quota)) * 100)));
            if (fill) fill.style.width = percent + '%';
            if (bar) {
                bar.setAttribute('aria-valuemin', '0');
                bar.setAttribute('aria-valuemax', String(data.quota || 100));
                bar.setAttribute('aria-valuenow', String(data.used || 0));
                const widget = document.getElementById('usage_widget');
                if (widget) {
                    widget.classList.remove('usage--warn', 'usage--danger');
                    if (percent >= 90) widget.classList.add('usage--danger');
                    else if (percent >= 70) widget.classList.add('usage--warn');
                }
            }
            const limitReached = data.used >= data.quota;
            const startBtn = document.getElementById('start-batch');
            if (startBtn) startBtn.disabled = limitReached;
            const startHelper = document.getElementById('start-helper');
            if (startHelper) {
                if (limitReached) startHelper.textContent = 'Daily request limit reached. Try again tomorrow.';
                else if (startHelper.textContent.includes('Daily request limit')) startHelper.textContent = '';
            }
            if (limitReached) {
                console.warn('Daily request limit reached.');
            }
        } catch (e) { /* ignore */ }
    }
})();
