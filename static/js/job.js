'use strict';
(function () {
    const $ = (id) => document.getElementById(id);

    window.state = window.state || { file: null, parsed: null, jobId: null, results: [], page: 1, perPage: 100 };
    window.usageInterval = window.usageInterval || null;

    window.startJob = async function startJob(keywords) {
        const startBtn = document.getElementById('start-batch');
        if (startBtn) {
            startBtn.setAttribute('data-loading', 'true');
            startBtn.dataset.originalText = startBtn.textContent;
            startBtn.textContent = 'Starting…';
            startBtn.disabled = true;
        }
        const config = {
            max_pages: Math.max(1, parseInt($('max_pages').value || '10') || 10),
            results_per_page: 10,
            include_organic: $('include_organic').checked,
            include_paa: $('include_paa').checked,
            include_related: $('include_related').checked,
            include_ads: $('include_ads').checked,
            include_ai_overview: $('include_ai_overview').checked,
            profile_sites: (window.getSelectedProfileSites ? window.getSelectedProfileSites() : [])
        };
        const payload = { keywords, config };
        const res = await fetch('/api/start-scraping', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        if (!res.ok) {
            if (res.status === 429) { const d = await res.json().catch(() => ({})); alert(d.detail || 'Daily request limit reached. Please try again tomorrow.'); if (window.refreshUsage) window.refreshUsage(); return; }
            alert('Failed to start job');
            if (startBtn) {
                startBtn.removeAttribute('data-loading');
                startBtn.textContent = startBtn.dataset.originalText || 'Start extraction';
                startBtn.disabled = false;
            }
            return;
        }
        const data = await res.json();
        window.state.jobId = data.job_id;
        window.state.startTime = Date.now();
        window.showProgressBar();
        window.updateProgressBar(0, 'Initializing search...', 'pending');
        if (window.usageInterval) { clearInterval(window.usageInterval); }
        window.usageInterval = setInterval(window.refreshUsage, 1200);
        window.pollStatus();
        // Pause/resume usage polling based on tab visibility
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                if (window.usageInterval) { clearInterval(window.usageInterval); window.usageInterval = null; }
            } else {
                if (!window.usageInterval && window.refreshUsage) { window.usageInterval = setInterval(window.refreshUsage, 1500); }
            }
        }, { once: true });
    }

    window.pollStatus = async function pollStatus() {
        if (!window.state.jobId) return;
        const res = await fetch(`/api/job-status/${window.state.jobId}`);
        if (!res.ok) return;
        const s = await res.json();
        const pct = s.progress || 0;
        window.updateProgressStats(s);
        window.updateProgressBar(pct, s.status, s);
        // Update start button state through lifecycle
        const startBtn = document.getElementById('start-batch');
        if (startBtn) {
            if (s.status === 'running' && pct > 5) { startBtn.textContent = 'Running…'; startBtn.setAttribute('data-loading', 'true'); startBtn.disabled = true; }
        }
        if (window.refreshUsage) window.refreshUsage();
        if (s.status === 'completed') {
            if (window.usageInterval) { clearInterval(window.usageInterval); window.usageInterval = null; }
            window.loadResults();
            const startBtn = document.getElementById('start-batch');
            if (startBtn) {
                startBtn.setAttribute('data-status', 'success');
                startBtn.textContent = '✓ Extracted';
                setTimeout(() => {
                    startBtn.removeAttribute('data-status');
                    startBtn.removeAttribute('data-loading');
                    startBtn.textContent = startBtn.dataset.originalText || 'Start extraction';
                    startBtn.disabled = false;
                }, 900);
            }
        } else if (s.status === 'failed') {
            if (window.usageInterval) { clearInterval(window.usageInterval); window.usageInterval = null; }
            setTimeout(() => {
                const jobError = document.getElementById('job-error');
                if (jobError) {
                    jobError.style.display = 'block';
                    jobError.textContent = 'Job failed: ' + (s.error_message || 'Unknown error');
                    jobError.focus && jobError.focus();
                } else {
                    alert('Job failed: ' + (s.error_message || ''));
                }
            }, 500);
            const startBtn = document.getElementById('start-batch');
            if (startBtn) {
                startBtn.setAttribute('data-status', 'error');
                startBtn.removeAttribute('data-loading');
                startBtn.textContent = startBtn.dataset.originalText || 'Start extraction';
                startBtn.disabled = false;
            }
        } else {
            setTimeout(window.pollStatus, 1200);
        }
    }

    window.showProgressBar = function showProgressBar() { $('progress-container').style.display = 'block'; }
    window.hideProgressBar = function hideProgressBar() { $('progress-container').style.display = 'none'; }

    window.updateProgressBar = function updateProgressBar(percentage, status, jobData) {
        const progressFill = $('progress-fill');
        const progressPercentage = $('progress-percentage');
        const progressStatusText = $('progress-status-text');
        const progressStatusIcon = $('progress-status-icon');
        const progressContainer = $('progress-container');
        const progressBar = $('progress-bar');
        progressFill.style.width = `${percentage}%`;
        progressPercentage.textContent = `${Math.round(percentage)}%`;
        if (progressBar) progressBar.setAttribute('aria-valuetext', `${Math.round(percentage)}%`);
        const statusInfo = window.getStatusInfo(status, jobData);
        progressStatusText.textContent = statusInfo.text;
        progressStatusIcon.textContent = statusInfo.icon;
        progressStatusIcon.className = `progress-status-icon ${statusInfo.iconClass}`;
        progressContainer.className = `progress-container ${statusInfo.containerClass}`;
        if (statusInfo.indeterminate) { progressBar.classList.add('indeterminate'); } else { progressBar.classList.remove('indeterminate'); }
    }

    window.updateProgressStats = function updateProgressStats(jobData) {
        const completed = jobData.completed_keywords || 0;
        const total = jobData.total_keywords || 0;
        const results = jobData.results_count || 0;
        const status = jobData.status || 'unknown';
        const currentKeyword = jobData.current_keyword;
        const processingSpeed = jobData.processing_speed;
        const estimatedRemaining = jobData.estimated_time_remaining;
        $('progress-keywords').textContent = `${completed} / ${total}`;
        $('progress-results').textContent = results.toLocaleString();
        $('progress-job-status').textContent = status.charAt(0).toUpperCase() + status.slice(1);
        let timeInfo = '';
        if (window.state.startTime) {
            const elapsed = Math.floor((Date.now() - window.state.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            timeInfo = `Elapsed: ${minutes}:${seconds.toString().padStart(2, '0')}`;
            if (estimatedRemaining && status === 'running') {
                const remainingMinutes = Math.floor(estimatedRemaining / 60);
                const remainingSeconds = estimatedRemaining % 60;
                timeInfo += ` • ETA: ${remainingMinutes}:${remainingSeconds.toString().padStart(2, '0')}`;
            }
            if (processingSpeed && status === 'running') { timeInfo += ` • Speed: ${processingSpeed.toFixed(1)} kw/min`; }
        }
        $('progress-time').textContent = timeInfo;
        if (currentKeyword && status === 'running') {
            const statusText = $('progress-status-text');
            const currentText = statusText.textContent;
            if (!currentText.includes(currentKeyword)) { statusText.textContent = `Processing: "${currentKeyword}"...`; }
        }
    }

    window.getStatusInfo = function getStatusInfo(status, jobData) {
        const p = jobData?.progress || 0;
        switch (status) {
            case 'pending': return { text: 'Queueing job…', icon: '⟳', iconClass: 'loading', containerClass: '', indeterminate: true };
            case 'running':
                if (p < 5) return { text: 'Preparing environment…', icon: '⟳', iconClass: 'loading', containerClass: '', indeterminate: true };
                else if (p < 15) return { text: 'Starting crawler…', icon: '⟳', iconClass: 'loading', containerClass: '', indeterminate: true };
                else if (p < 90) {
                    const completed = jobData?.completed_keywords || 0;
                    const total = jobData?.total_keywords || 0;
                    return { text: `Fetching results (${completed}/${total} keywords)…`, icon: '⟳', iconClass: 'loading', containerClass: '', indeterminate: false };
                } else { return { text: 'Finalizing output…', icon: '⟳', iconClass: 'loading', containerClass: '', indeterminate: false }; }
            case 'completed': return { text: 'Extraction completed successfully!', icon: '✓', iconClass: 'success', containerClass: 'success', indeterminate: false };
            case 'failed': return { text: `Extraction failed: ${jobData?.error_message || 'Unknown error'}`, icon: '✗', iconClass: 'error', containerClass: 'error', indeterminate: false };
            default: return { text: 'Ready to start', icon: '⟳', iconClass: 'loading', containerClass: '', indeterminate: false };
        }
    }

    window.setIndeterminate = function setIndeterminate(isIndeterminate) {
        const bar = document.getElementById('progress-bar');
        if (!bar) return; if (isIndeterminate) bar.classList.add('indeterminate'); else bar.classList.remove('indeterminate');
    }

    window.deriveStageFromStatus = function deriveStageFromStatus(s) {
        const p = s.progress || 0;
        if (s.status === 'pending') return { label: 'Queueing job…', indeterminate: true };
        if (s.status === 'running') {
            if (p < 5) return { label: 'Preparing environment… (pulling image, starting container)', indeterminate: true };
            if (p < 15) return { label: 'Starting crawler…', indeterminate: true };
            if (p < 90) return { label: `Scraping keywords… ${s.completed_keywords || 0}/${s.total_keywords || 0}`, indeterminate: false };
            return { label: 'Finalizing results…', indeterminate: false };
        }
        if (s.status === 'completed') return { label: 'Completed', indeterminate: false };
        if (s.status === 'failed') return { label: 'Failed', indeterminate: false };
        return { label: '', indeterminate: false };
    }
})();
