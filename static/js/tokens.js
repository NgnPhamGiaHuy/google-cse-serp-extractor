'use strict';
(function () {
    const $ = (id) => document.getElementById(id);

    window.tokenState = {
        hasValidTokens: false,
        tokens: { google_api_key: null, google_cx: null }
    };

    window.checkTokenStatus = async function checkTokenStatus() {
        try {
            const response = await fetch('/api/token-status');
            const data = await response.json();
            if (data.success) {
                const status = data.status;
                const hasGoogle = status.google_api_key.has_env || status.google_api_key.has_temp;
                const hasCx = status.google_cx.has_env || status.google_cx.has_temp;
                if (hasGoogle && hasCx) {
                    tokenState.hasValidTokens = true;
                    $('token-card').style.display = 'none';
                    $('upload-card').style.display = 'block';
                    if (window.state && state.results && state.results.length > 0) {
                        $('results-section').style.display = 'block';
                    }
                    return;
                }
            }
            $('token-card').style.display = 'block';
            $('upload-card').style.display = 'none';
            $('results-section').style.display = 'none';
            window.updateTokenStatus();
        } catch (error) {
            console.error('Failed to check token status:', error);
            $('token-card').style.display = 'block';
            $('upload-card').style.display = 'none';
            $('results-section').style.display = 'none';
        }
    }

    window.updateTokenStatus = function updateTokenStatus() {
        const status = $('token-status');
        const hasGoogle = $('google-api-key').value.trim();
        const hasCx = $('google-cx').value.trim();
        if (hasGoogle && hasCx) {
            status.textContent = '✓ Google API configuration complete';
            status.style.color = 'var(--accent)';
        } else {
            status.textContent = 'Please configure your Google API credentials to start scraping';
            status.style.color = 'var(--muted)';
        }
    }

    window.saveTokens = async function saveTokens() {
        const saveBtn = document.getElementById('save-tokens');
        if (saveBtn) { saveBtn.setAttribute('data-loading', 'true'); saveBtn.dataset.originalText = saveBtn.textContent; saveBtn.textContent = 'Saving…'; saveBtn.disabled = true; }
        const tokens = {
            google_api_key: $('google-api-key').value.trim(),
            google_cx: $('google-cx').value.trim()
        };
        if (!tokens.google_api_key || !tokens.google_cx) {
            alert('Google API Key and CSE ID are required');
            if (saveBtn) { saveBtn.removeAttribute('data-loading'); saveBtn.textContent = saveBtn.dataset.originalText || 'Save tokens'; saveBtn.disabled = false; }
            return;
        }
        try {
            for (const [tokenType, tokenValue] of Object.entries(tokens)) {
                if (tokenValue) {
                    const formData = new FormData();
                    formData.append('token_type', tokenType);
                    formData.append('token_value', tokenValue);
                    const response = await fetch('/api/set-token', { method: 'POST', body: formData });
                    const result = await response.json();
                    if (!result.success) { alert(`Failed to save ${tokenType}: ${result.message}`); return; }
                }
            }
            await window.checkTokenStatus();
            if (saveBtn) { saveBtn.setAttribute('data-status', 'success'); saveBtn.textContent = 'Saved'; setTimeout(() => { saveBtn.removeAttribute('data-status'); saveBtn.removeAttribute('data-loading'); saveBtn.textContent = saveBtn.dataset.originalText || 'Save tokens'; saveBtn.disabled = false; }, 900); }
            alert('✅ Tokens saved successfully!\n\nYou can now continue using the tool with your new API key.');
            if (tokens.google_api_key && tokens.google_cx) {
                const tokenCard = document.getElementById('token-card');
                const uploadCard = document.getElementById('upload-card');
                if (tokenCard && uploadCard) {
                    tokenCard.style.display = 'none';
                    uploadCard.style.display = 'block';
                    if (window.hideQuotaError) window.hideQuotaError();
                    if (!window.state || !state.results || state.results.length === 0) {
                        if (window.clearJobState) window.clearJobState();
                    } else {
                        $('results-section').style.display = 'block';
                    }
                    if (window.resetUploadForm) window.resetUploadForm();
                    uploadCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        } catch (error) {
            console.error('Failed to save tokens:', error);
            if (saveBtn) { saveBtn.setAttribute('data-status', 'error'); saveBtn.textContent = 'Save failed'; setTimeout(() => { saveBtn.removeAttribute('data-status'); saveBtn.removeAttribute('data-loading'); saveBtn.textContent = saveBtn.dataset.originalText || 'Save tokens'; saveBtn.disabled = false; }, 1200); }
            alert('Failed to save tokens. Please try again.');
        }
    }

    window.validateTokens = async function validateTokens() {
        const validateBtn = document.getElementById('validate-tokens');
        if (validateBtn) { validateBtn.setAttribute('data-loading', 'true'); validateBtn.dataset.originalText = validateBtn.textContent; validateBtn.textContent = 'Validating…'; validateBtn.disabled = true; }
        const tokens = {
            google_api_key: $('google-api-key').value.trim(),
            google_cx: $('google-cx').value.trim()
        };
        if (!tokens.google_api_key || !tokens.google_cx) { alert('Google API Key and CSE ID are required for validation'); if (validateBtn) { validateBtn.removeAttribute('data-loading'); validateBtn.textContent = validateBtn.dataset.originalText || 'Validate tokens'; validateBtn.disabled = false; } return; }
        try {
            const results = [];
            if (tokens.google_api_key) {
                const formData = new FormData();
                formData.append('token_type', 'google_api_key');
                formData.append('token_value', tokens.google_api_key);
                const response = await fetch('/api/validate-token', { method: 'POST', body: formData });
                const result = await response.json();
                results.push(`Google API Key: ${result.valid ? '✓' : '✗'} ${result.message}`);
            }
            alert(results.join('\n'));
            if (validateBtn) { validateBtn.setAttribute('data-status', 'success'); validateBtn.textContent = 'Validated'; setTimeout(() => { validateBtn.removeAttribute('data-status'); validateBtn.removeAttribute('data-loading'); validateBtn.textContent = validateBtn.dataset.originalText || 'Validate tokens'; validateBtn.disabled = false; }, 900); }
        } catch (error) {
            console.error('Failed to validate tokens:', error);
            if (validateBtn) { validateBtn.setAttribute('data-status', 'error'); validateBtn.textContent = 'Validation failed'; setTimeout(() => { validateBtn.removeAttribute('data-status'); validateBtn.removeAttribute('data-loading'); validateBtn.textContent = validateBtn.dataset.originalText || 'Validate tokens'; validateBtn.disabled = false; }, 1200); }
            alert('Failed to validate tokens. Please try again.');
        }
    }

    window.clearTokens = async function clearTokens() {
        const clearBtn = document.getElementById('clear-tokens');
        if (!confirm('Are you sure you want to clear all tokens?')) { return; }
        if (clearBtn) { clearBtn.setAttribute('data-loading', 'true'); clearBtn.dataset.originalText = clearBtn.textContent; clearBtn.textContent = 'Clearing…'; clearBtn.disabled = true; }
        try {
            const response = await fetch('/api/clear-tokens', { method: 'DELETE' });
            const result = await response.json();
            if (result.success) {
                $('google-api-key').value = '';
                $('google-cx').value = '';
                window.updateTokenStatus();
                alert('All tokens cleared');
                if (clearBtn) { clearBtn.setAttribute('data-status', 'success'); clearBtn.textContent = 'Cleared'; setTimeout(() => { clearBtn.removeAttribute('data-status'); clearBtn.removeAttribute('data-loading'); clearBtn.textContent = clearBtn.dataset.originalText || 'Clear tokens'; clearBtn.disabled = false; }, 900); }
            } else { alert('Failed to clear tokens'); }
        } catch (error) {
            console.error('Failed to clear tokens:', error);
            if (clearBtn) { clearBtn.setAttribute('data-status', 'error'); clearBtn.textContent = 'Clear failed'; setTimeout(() => { clearBtn.removeAttribute('data-status'); clearBtn.removeAttribute('data-loading'); clearBtn.textContent = clearBtn.dataset.originalText || 'Clear tokens'; clearBtn.disabled = false; }, 1200); }
            alert('Failed to clear tokens. Please try again.');
        }
    }

    // backup tokens
    window.saveBackupTokens = async function saveBackupTokens() {
        const saveBtn = document.getElementById('save-backup-tokens');
        if (saveBtn) { saveBtn.setAttribute('data-loading', 'true'); saveBtn.dataset.originalText = saveBtn.textContent; saveBtn.textContent = 'Saving…'; saveBtn.disabled = true; }
        const backupTokens = { google_api_key: $('backup-google-api-key').value.trim(), google_cx: $('backup-google-cx').value.trim() };
        try {
            for (const [tokenType, tokenValue] of Object.entries(backupTokens)) {
                if (tokenValue) {
                    const formData = new FormData();
                    formData.append('token_type', tokenType);
                    formData.append('token_value', tokenValue);
                    const response = await fetch('/api/set-backup-token', { method: 'POST', body: formData });
                    const result = await response.json();
                    if (!result.success) { alert(`Failed to save backup ${tokenType}: ${result.message}`); return; }
                }
            }
            alert('Backup tokens saved successfully!');
            if (saveBtn) { saveBtn.setAttribute('data-status', 'success'); saveBtn.textContent = 'Saved'; setTimeout(() => { saveBtn.removeAttribute('data-status'); saveBtn.removeAttribute('data-loading'); saveBtn.textContent = saveBtn.dataset.originalText || 'Save backup tokens'; saveBtn.disabled = false; }, 900); }
        } catch (error) {
            console.error('Failed to save backup tokens:', error);
            if (saveBtn) { saveBtn.setAttribute('data-status', 'error'); saveBtn.textContent = 'Save failed'; setTimeout(() => { saveBtn.removeAttribute('data-status'); saveBtn.removeAttribute('data-loading'); saveBtn.textContent = saveBtn.dataset.originalText || 'Save backup tokens'; saveBtn.disabled = false; }, 1200); }
            alert('Failed to save backup tokens. Please try again.');
        }
    }

    window.validateBackupTokens = async function validateBackupTokens() {
        const validateBtn = document.getElementById('validate-backup-tokens');
        if (validateBtn) { validateBtn.setAttribute('data-loading', 'true'); validateBtn.dataset.originalText = validateBtn.textContent; validateBtn.textContent = 'Validating…'; validateBtn.disabled = true; }
        const backupTokens = { google_api_key: $('backup-google-api-key').value.trim(), google_cx: $('backup-google-cx').value.trim() };
        try {
            const results = [];
            for (const [tokenType, tokenValue] of Object.entries(backupTokens)) {
                if (tokenValue) {
                    const formData = new FormData();
                    formData.append('token_type', tokenType);
                    formData.append('token_value', tokenValue);
                    const response = await fetch('/api/validate-token', { method: 'POST', body: formData });
                    const result = await response.json();
                    if (result.valid) results.push(`✓ Backup ${tokenType}: ${result.message}`);
                    else results.push(`✗ Backup ${tokenType}: ${result.message}`);
                }
            }
            if (results.length === 0) alert('No backup tokens to validate'); else alert(results.join('\n'));
            if (validateBtn) { validateBtn.setAttribute('data-status', 'success'); validateBtn.textContent = 'Validated'; setTimeout(() => { validateBtn.removeAttribute('data-status'); validateBtn.removeAttribute('data-loading'); validateBtn.textContent = validateBtn.dataset.originalText || 'Validate backup tokens'; validateBtn.disabled = false; }, 900); }
        } catch (error) {
            console.error('Failed to validate backup tokens:', error);
            if (validateBtn) { validateBtn.setAttribute('data-status', 'error'); validateBtn.textContent = 'Validation failed'; setTimeout(() => { validateBtn.removeAttribute('data-status'); validateBtn.removeAttribute('data-loading'); validateBtn.textContent = validateBtn.dataset.originalText || 'Validate backup tokens'; validateBtn.disabled = false; }, 1200); }
            alert('Failed to validate backup tokens. Please try again.');
        }
    }

    window.clearBackupTokens = async function clearBackupTokens() {
        const clearBtn = document.getElementById('clear-backup-tokens');
        if (!confirm('Are you sure you want to clear all backup tokens?')) { return; }
        if (clearBtn) { clearBtn.setAttribute('data-loading', 'true'); clearBtn.dataset.originalText = clearBtn.textContent; clearBtn.textContent = 'Clearing…'; clearBtn.disabled = true; }
        try {
            const response = await fetch('/api/clear-backup-tokens', { method: 'DELETE' });
            const result = await response.json();
            if (result.success) {
                alert('Backup tokens cleared successfully');
                $('backup-google-api-key').value = '';
                $('backup-google-cx').value = '';
                if (clearBtn) { clearBtn.setAttribute('data-status', 'success'); clearBtn.textContent = 'Cleared'; setTimeout(() => { clearBtn.removeAttribute('data-status'); clearBtn.removeAttribute('data-loading'); clearBtn.textContent = clearBtn.dataset.originalText || 'Clear backup tokens'; clearBtn.disabled = false; }, 900); }
            } else { alert('Failed to clear backup tokens'); }
        } catch (error) {
            console.error('Failed to clear backup tokens:', error);
            if (clearBtn) { clearBtn.setAttribute('data-status', 'error'); clearBtn.textContent = 'Clear failed'; setTimeout(() => { clearBtn.removeAttribute('data-status'); clearBtn.removeAttribute('data-loading'); clearBtn.textContent = clearBtn.dataset.originalText || 'Clear backup tokens'; clearBtn.disabled = false; }, 1200); }
            alert('Failed to clear backup tokens. Please try again.');
        }
    }

})();
