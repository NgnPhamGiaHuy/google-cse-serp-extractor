'use strict';
(function () {
    const $ = (id) => document.getElementById(id);

    window.initializeFileUpload = function initializeFileUpload() {
        const dz = document.getElementById('dropzone');
        function openPicker() { document.getElementById('file-input').click(); }
        dz.addEventListener('click', openPicker);
        dz.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openPicker(); } });
        ['dragenter', 'dragover'].forEach(ev => dz.addEventListener(ev, (e) => { e.preventDefault(); e.stopPropagation(); dz.classList.add('dragover'); }));
        ['dragleave', 'dragend', 'drop'].forEach(ev => dz.addEventListener(ev, (e) => { e.preventDefault(); e.stopPropagation(); dz.classList.remove('dragover'); }));
        dz.addEventListener('drop', (e) => {
            const files = e.dataTransfer?.files; if (!files || !files.length) return;
            document.getElementById('file-input').files = files;
            document.getElementById('file-input').dispatchEvent(new Event('change'));
        });

        $('file-input').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            window.state.file = file || null;
            $('file-meta').textContent = file ? `${file.name} · ${(file.size / 1024).toFixed(1)} KB` : '';
            if (!file) return;
            const form = new FormData();
            form.append('file', file);
            const res = await fetch('/api/upload-keywords', { method: 'POST', body: form });
            const data = await res.json();
            if (!res.ok || !data.success) {
                $('validation-errors').textContent = data.detail || 'We couldn’t read the file. Check the format and try again.';
                $('file-preview').style.display = 'block';
                $('preview-table').innerHTML = '';
                return;
            }
            window.state.parsed = data;
            $('validation-errors').textContent = '';
            $('file-preview').style.display = 'block';
            if (window.updateFilePreview) window.updateFilePreview();
        });
    }
})();
