'use strict';
(function () {
    const $ = (id) => document.getElementById(id);

    window.showQuotaError = function showQuotaError(quotaErrorData) {
        const container = document.getElementById('quota-error-container');
        const section = document.getElementById('quota-error-section');
        if (!quotaErrorData || !container || !section) return;
        const timestamp = quotaErrorData.occurred_at ? new Date(quotaErrorData.occurred_at).toLocaleString() : new Date().toLocaleString();
        const quotaLimit = quotaErrorData.quota_limit || 'Unknown';
        const quotaMetric = quotaErrorData.quota_metric || 'queries';
        const affectedKeyword = quotaErrorData.affected_keyword || 'Unknown';
        const helpLinks = quotaErrorData.help_links || [];
        const isLongKeyword = affectedKeyword.length > 80;
        container.innerHTML = `
                <div class="quota-error">
                    <div class="quota-error-timestamp">${timestamp}</div>
                    <div class="quota-error-header">
                        <div class="quota-error-icon">⚠</div>
                        <h3 class="quota-error-title">Daily Quota Limit Reached</h3>
                    </div>
                    <p class="quota-error-message">
                        ${quotaErrorData.message || 'Google CSE daily query limit has been reached. Please try again tomorrow or use a new API key.'}
                    </p>
                    <div class="quota-error-details">
                        <div class="quota-error-detail-item">
                            <span class="quota-error-detail-label">Quota Limit:</span>
                            <span class="quota-error-detail-value">${quotaLimit} ${quotaMetric}/day</span>
                        </div>
                        <div class="quota-error-detail-item">
                            <span class="quota-error-detail-label">Affected Keyword:</span>
                            <span class="quota-error-detail-value ${isLongKeyword ? 'long-keyword' : ''}" title="${affectedKeyword}">"${affectedKeyword}"</span>
                        </div>
                        <div class="quota-error-detail-item">
                            <span class="quota-error-detail-label">Error Type:</span>
                            <span class="quota-error-detail-value">${quotaErrorData.error_type || 'quota_exceeded'}</span>
                        </div>
                    </div>
                    <div class="quota-error-actions">
                        <button class="quota-error-action" onclick="showTokenManagement()" id="change-api-key-btn">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                <circle cx="12" cy="16" r="1"></circle>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                            </svg>
                            Change API Key
                        </button>
                        <button class="quota-error-action secondary" onclick="hideQuotaError()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                            Dismiss
                        </button>
                    </div>
                    ${helpLinks.length > 0 ? `
                        <div class="quota-error-help-links">
                            <div class="quota-error-help-links-title">Helpful Links:</div>
                            <ul class="quota-error-help-links-list">
                                ${helpLinks.map(link => `
                                    <li>
                                        <a href="${link}" target="_blank" rel="noopener noreferrer">
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                                <polyline points="15,3 21,3 21,9"></polyline>
                                                <line x1="10" y1="14" x2="21" y2="3"></line>
                                            </svg>
                                            ${window.getLinkDescription(link)}
                                        </a>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        section.style.display = 'block';
        const changeBtn = document.getElementById('change-api-key-btn');
        if (changeBtn) {
            changeBtn.addEventListener('click', function (e) { e.preventDefault(); window.showTokenManagement(); });
        }
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    window.hideQuotaError = function hideQuotaError() {
        const section = document.getElementById('quota-error-section');
        if (section) { section.style.display = 'none'; }
    }

    window.clearJobState = function clearJobState() {
        window.state.jobId = null;
        window.state.isRunning = false;
        const progressContainer = document.getElementById('progress-container'); if (progressContainer) { progressContainer.style.display = 'none'; }
        const resultsSection = document.getElementById('results-section'); if (resultsSection) { resultsSection.style.display = 'none'; }
        const resultsList = document.getElementById('results-list'); if (resultsList) { resultsList.style.display = 'none'; }
        const progressTitle = document.getElementById('progress-title');
        const progressPercentage = document.getElementById('progress-percentage');
        const progressFill = document.getElementById('progress-fill');
        const progressStatusIcon = document.getElementById('progress-status-icon');
        const progressStatusText = document.getElementById('progress-status-text');
        const progressKeywords = document.getElementById('progress-keywords');
        const progressResults = document.getElementById('progress-results');
        const progressJobStatus = document.getElementById('progress-job-status');
        const progressTime = document.getElementById('progress-time');
        if (progressTitle) progressTitle.textContent = 'Extraction Progress';
        if (progressPercentage) progressPercentage.textContent = '0%';
        if (progressFill) progressFill.style.width = '0%';
        if (progressStatusIcon) { progressStatusIcon.className = 'progress-status-icon'; progressStatusIcon.textContent = ''; }
        if (progressStatusText) progressStatusText.textContent = 'Ready to start extraction...';
        if (progressKeywords) progressKeywords.textContent = '0 / 0';
        if (progressResults) progressResults.textContent = '0';
        if (progressJobStatus) progressJobStatus.textContent = 'Ready';
        if (progressTime) progressTime.textContent = 'Elapsed: 0:00';
        if (progressContainer) { progressContainer.className = 'progress-container'; }
    }

    window.resetUploadForm = function resetUploadForm() {
        const fileInput = document.getElementById('file-input'); if (fileInput) { fileInput.value = ''; }
        const preview = document.getElementById('preview'); if (preview) { preview.innerHTML = ''; }
        const uploadBtn = document.getElementById('upload-btn'); if (uploadBtn) { uploadBtn.disabled = false; uploadBtn.textContent = 'Start Extraction'; }
        const errorMsg = document.getElementById('error-msg'); if (errorMsg) { errorMsg.textContent = ''; errorMsg.style.display = 'none'; }
    }

    window.showTokenManagement = async function showTokenManagement() {
        const changeBtn = document.getElementById('change-api-key-btn');
        let originalText = '';
        if (changeBtn) {
            originalText = changeBtn.innerHTML;
            changeBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="animate-spin">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 6v6l4 2"></path>
                    </svg>
                    Processing...
                `;
            changeBtn.disabled = true;
        }
        window.clearJobState();
        window.resetUploadForm();
        window.hideQuotaError();
        try {
            $('google-api-key').value = '';
            $('google-cx').value = '';
            const clearResponse = await fetch('/api/clear-tokens', { method: 'DELETE' });
            const clearResult = await clearResponse.json();
            if (!clearResult.success) { console.warn('Failed to clear temporary tokens:', clearResult.message); }
            const tokenCard = document.getElementById('token-card');
            const uploadCard = document.getElementById('upload-card');
            const resultsSection = document.getElementById('results-section');
            if (tokenCard && uploadCard) {
                tokenCard.style.display = 'block';
                uploadCard.style.display = 'none';
                if (resultsSection) { resultsSection.style.display = 'none'; }
                window.updateTokenStatusWithQuotaMessage();
                setTimeout(() => { $('google-api-key').focus(); $('google-api-key').select(); }, 100);
                tokenCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        } catch (error) {
            console.error('Failed to clear tokens:', error);
            const tokenCard = document.getElementById('token-card');
            const uploadCard = document.getElementById('upload-card');
            const resultsSection = document.getElementById('results-section');
            if (tokenCard && uploadCard) {
                tokenCard.style.display = 'block';
                uploadCard.style.display = 'none';
                if (resultsSection) { resultsSection.style.display = 'none'; }
                window.updateTokenStatusWithQuotaMessage();
                tokenCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        } finally {
            if (changeBtn) { changeBtn.innerHTML = originalText; changeBtn.disabled = false; }
        }
    }

    window.updateTokenStatusWithQuotaMessage = function updateTokenStatusWithQuotaMessage() {
        const status = $('token-status');
        status.innerHTML = '⚠ <strong>Quota exceeded detected!</strong> Please enter a new Google API key below.';
        status.style.color = '#dc2626';
        status.style.fontWeight = '500';
        status.style.backgroundColor = '#fef2f2';
        status.style.padding = '8px 12px';
        status.style.borderRadius = '6px';
        status.style.border = '1px solid #fecaca';
    }

    window.getLinkDescription = function getLinkDescription(url) {
        if (url.includes('cloud.google.com/docs/quotas')) { return 'Request Higher Quota Limit'; }
        else if (url.includes('console.cloud.google.com')) { return 'Google Cloud Console'; }
        else if (url.includes('cse.google.com')) { return 'Google Custom Search Engine'; }
        else { return 'Learn More'; }
    }

    document.addEventListener('DOMContentLoaded', function () {
        const changeBtn = document.getElementById('change-api-key-btn');
        if (changeBtn) { changeBtn.addEventListener('click', function (e) { e.preventDefault(); window.showTokenManagement(); }); }
    });

    // Enhanced pollStatus to check for quota errors: wrap original if defined later
    const defineQuotaAwarePoll = () => {
        if (!window.pollStatus || window.pollStatus.__quotaWrapped) return;
        const originalPollStatus = window.pollStatus;
        const wrapped = async function () {
            if (!window.state.jobId) return;
            const res = await fetch(`/api/job-status/${window.state.jobId}`);
            if (!res.ok) return;
            const s = await res.json();
            if (s.quota_error_display) { window.showQuotaError(s.quota_error_display); }
            return originalPollStatus();
        };
        wrapped.__quotaWrapped = true;
        window.pollStatus = wrapped;
    };
    // Try at load; main.js will call again after all modules inited
    defineQuotaAwarePoll();
    window.__enableQuotaAwarePoll = defineQuotaAwarePoll;
})();
