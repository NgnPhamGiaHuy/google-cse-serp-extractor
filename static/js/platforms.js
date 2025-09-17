'use strict';
(function () {
    const $ = (id) => document.getElementById(id);

    window.platformSuggestions = [
        { name: 'LinkedIn', domain: 'linkedin.com/in', siteFilter: 'site:linkedin.com/in' },
        { name: 'LinkedIn Vietnam', domain: 'vn.linkedin.com/in', siteFilter: 'site:vn.linkedin.com/in' },
        { name: 'Facebook', domain: 'facebook.com', siteFilter: 'site:facebook.com' },
        { name: 'GitHub', domain: 'github.com', siteFilter: 'site:github.com' },
        { name: 'Twitter', domain: 'twitter.com', siteFilter: 'site:twitter.com' },
        { name: 'Instagram', domain: 'instagram.com', siteFilter: 'site:instagram.com' },
        { name: 'Stack Overflow', domain: 'stackoverflow.com', siteFilter: 'site:stackoverflow.com' },
        { name: 'Reddit', domain: 'reddit.com', siteFilter: 'site:reddit.com' },
        { name: 'YouTube', domain: 'youtube.com', siteFilter: 'site:youtube.com' },
        { name: 'Medium', domain: 'medium.com', siteFilter: 'site:medium.com' },
        { name: 'Dev.to', domain: 'dev.to', siteFilter: 'site:dev.to' },
        { name: 'Behance', domain: 'behance.net', siteFilter: 'site:behance.net' },
        { name: 'Dribbble', domain: 'dribbble.com', siteFilter: 'site:dribbble.com' },
        { name: 'AngelList', domain: 'angel.co', siteFilter: 'site:angel.co' },
        { name: 'Crunchbase', domain: 'crunchbase.com', siteFilter: 'site:crunchbase.com' }
    ];

    window.selectedPlatforms = new Map();
    window.suggestionTimeout = null;

    window.convertPlatformToSiteFilter = async function convertPlatformToSiteFilter(platformName) {
        const normalized = platformName.toLowerCase().trim();
        if (normalized.startsWith('site:')) { return normalized; }
        try {
            const formData = new FormData();
            formData.append('platform_name', platformName);
            const response = await fetch('/api/convert-platform', { method: 'POST', body: formData });
            const data = await response.json();
            if (data.success) { return data.site_filter; }
        } catch (error) { console.warn('Failed to convert platform via API:', error); }
        const suggestion = platformSuggestions.find(p => p.name.toLowerCase() === normalized || p.domain.toLowerCase().includes(normalized));
        if (suggestion) { return suggestion.siteFilter; }
        let domain = normalized;
        if (!domain.includes('.') && !domain.includes(' ')) { domain = domain + '.com'; }
        if (domain.includes('linkedin') && !domain.includes('/in')) { domain = domain.replace(/\/$/, '') + '/in'; }
        return `site:${domain}`;
    }

    window.validatePlatformName = function validatePlatformName(platformName) {
        if (!platformName || platformName.trim().length === 0) { return { valid: false, error: 'Platform name cannot be empty' }; }
        const normalized = platformName.toLowerCase().trim();
        if (!/^[a-zA-Z0-9\s\.\-_\/]+$/.test(normalized)) { return { valid: false, error: 'Platform name contains invalid characters' }; }
        if (selectedPlatforms.has(normalized)) { return { valid: false, error: 'Platform already selected' }; }
        return { valid: true };
    }

    window.showSuggestions = async function showSuggestions(query) {
        const suggestionsContainer = document.getElementById('platform-suggestions');
        if (!query || query.length < 1) { suggestionsContainer.style.display = 'none'; return; }
        try {
            const response = await fetch(`/api/platform-suggestions?query=${encodeURIComponent(query)}&limit=8`);
            const data = await response.json();
            if (!data.success || !data.suggestions || data.suggestions.length === 0) { suggestionsContainer.style.display = 'none'; return; }
            suggestionsContainer.innerHTML = data.suggestions.map(platform => `
                    <div class="platform-suggestion" data-platform='${JSON.stringify(platform)}'>
                        <span class="platform-suggestion-name">${platform.name}</span>
                        <span class="platform-suggestion-domain">${platform.domain}</span>
                    </div>
                `).join('');
            suggestionsContainer.style.display = 'block';
            suggestionsContainer.querySelectorAll('.platform-suggestion').forEach(el => {
                el.addEventListener('click', async () => {
                    const platform = JSON.parse(el.dataset.platform);
                    await window.addPlatform(platform.name);
                    document.getElementById('platform-input').value = '';
                    suggestionsContainer.style.display = 'none';
                });
            });
        } catch (error) { console.warn('Failed to fetch platform suggestions:', error); suggestionsContainer.style.display = 'none'; }
    }

    window.addPlatform = async function addPlatform(platformName) {
        const validation = window.validatePlatformName(platformName);
        if (!validation.valid) { window.showPlatformError(validation.error); return; }
        const normalized = platformName.toLowerCase().trim();
        const siteFilter = await window.convertPlatformToSiteFilter(platformName);
        const domain = siteFilter.replace('site:', '');
        selectedPlatforms.set(normalized, { name: platformName, domain: domain, siteFilter: siteFilter });
        window.renderSelectedPlatforms();
        window.hidePlatformError();
        window.savePlatforms();
        if (window.updateAllPreviews) window.updateAllPreviews();
    }

    window.removePlatform = function removePlatform(platformName) {
        const normalized = platformName.toLowerCase().trim();
        selectedPlatforms.delete(normalized);
        window.renderSelectedPlatforms();
        window.savePlatforms();
        if (window.updateAllPreviews) window.updateAllPreviews();
    }

    window.renderSelectedPlatforms = function renderSelectedPlatforms() {
        const container = document.getElementById('selected-platforms');
        container.innerHTML = Array.from(selectedPlatforms.values()).map(platform => `
                <div class="platform-tag" data-platform="${platform.name}">
                    <span class="platform-tag-name">${platform.name}</span>
                    <span class="platform-tag-domain">${platform.domain}</span>
                    <button type="button" class="platform-tag-remove" data-platform-name="${platform.name}" title="Remove platform">×</button>
                </div>
            `).join('');
    }

    window.showPlatformError = function showPlatformError(message) {
        const errorEl = document.getElementById('platform-error');
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }

    window.hidePlatformError = function hidePlatformError() {
        const errorEl = document.getElementById('platform-error');
        errorEl.style.display = 'none';
    }

    window.getSelectedProfileSites = function getSelectedProfileSites() {
        return Array.from(selectedPlatforms.values()).map(platform => platform.siteFilter);
    }

    window.loadPlatforms = async function loadPlatforms() {
        selectedPlatforms.clear();
        const saved = localStorage.getItem('profile_platforms');
        if (saved) {
            try {
                const platforms = JSON.parse(saved);
                platforms.forEach(platform => { selectedPlatforms.set(platform.name.toLowerCase(), platform); });
                window.renderSelectedPlatforms();
                if (window.updateAllPreviews) window.updateAllPreviews();
            } catch (e) { console.warn('Failed to load saved platforms:', e); }
        } else {
            window.renderSelectedPlatforms();
            if (window.updateAllPreviews) window.updateAllPreviews();
        }
    }

    window.savePlatforms = function savePlatforms() {
        const platforms = Array.from(selectedPlatforms.values());
        localStorage.setItem('profile_platforms', JSON.stringify(platforms));
    }

    window.initializePlatformInput = function initializePlatformInput() {
        const input = document.getElementById('platform-input');
        const addButton = document.getElementById('platform-add-btn');
        const suggestionsContainer = document.getElementById('platform-suggestions');

        async function addPlatformFromInput() {
            const value = input.value.trim();
            if (value) {
                await window.addPlatform(value);
                input.value = '';
                suggestionsContainer.style.display = 'none';
            } else {
                window.showPlatformError('Please enter a platform name before adding');
                input.focus();
                addButton.classList.add('error-state');
                input.classList.add('error-state');
                setTimeout(() => { addButton.classList.remove('error-state'); input.classList.remove('error-state'); }, 300);
            }
        }

        input.addEventListener('input', (e) => {
            clearTimeout(window.suggestionTimeout);
            window.suggestionTimeout = setTimeout(() => { window.showSuggestions(e.target.value); }, 150);
        });

        input.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') { e.preventDefault(); await addPlatformFromInput(); }
            else if (e.key === 'Escape') { suggestionsContainer.style.display = 'none'; e.target.blur(); }
        });

        addButton.addEventListener('click', async (e) => { e.preventDefault(); await addPlatformFromInput(); });

        document.addEventListener('click', (e) => { if (!e.target.closest('#platform-input-wrapper')) { suggestionsContainer.style.display = 'none'; } });

        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('platform-tag-remove')) {
                const platformName = e.target.getAttribute('data-platform-name');
                if (platformName) { window.removePlatform(platformName); }
            }
        });

        window.loadPlatforms();

        document.getElementById('copy-query-btn').addEventListener('click', window.copyQueryToClipboard);
        document.getElementById('manual-query').addEventListener('input', () => { if (window.updateAllPreviews) window.updateAllPreviews(); });
        document.getElementById('manual-query').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); const startBtn = document.getElementById('start-batch'); if (startBtn) startBtn.click(); }
        });
    }
})();
