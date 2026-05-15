document.addEventListener('DOMContentLoaded', () => {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabSaved = document.getElementById('tab-saved');
    const tabIgnored = document.getElementById('tab-ignored');
    const countSaved = document.getElementById('count-saved');
    const countIgnored = document.getElementById('count-ignored');
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error-msg');

    let vocabData = { saved: [], ignored: [] };

    // Tab switching logic
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const target = btn.getAttribute('data-tab');
            if (target === 'saved') {
                tabSaved.classList.remove('hidden');
                tabIgnored.classList.add('hidden');
            } else {
                tabIgnored.classList.remove('hidden');
                tabSaved.classList.add('hidden');
            }
        });
    });

    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }

    function formatDate(dateString) {
        const d = new Date(dateString);
        return `${d.getFullYear()}/${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
    }

    function formatTime(seconds) {
        if (seconds === undefined || seconds === null) return '';
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }

    function createVocabCard(item, index) {
        const card = document.createElement('div');
        card.className = 'vocab-card glass-panel';
        card.style.animationDelay = `${Math.min(index * 0.05, 0.5)}s`;
        
        let contextHtml = '';
        if (item.context) {
            // Context comes from data-text, which contains raw text (e.g., "[音楽]")
            const safeContext = escapeHtml(item.context);
            const safeWord = escapeHtml(item.word);
            // Simple string replacement for highlighting
            const highlightedContext = safeContext.split(safeWord).join(`<span style="color: var(--primary-color); font-weight: bold; background: rgba(139, 92, 246, 0.2); padding: 0 2px; border-radius: 4px;">${safeWord}</span>`);
            contextHtml = `<div class="vocab-context">${highlightedContext}</div>`;
        }
        
        const timestampStr = item.timestamp > 0 ? `🎬 ${formatTime(item.timestamp)}` : '';

        card.innerHTML = `
            <div class="vocab-word">${escapeHtml(item.word)}</div>
            ${contextHtml}
            <div class="vocab-meta">
                <span>${timestampStr}</span>
                <span>📅 ${formatDate(item.created_at)}</span>
            </div>
        `;
        return card;
    }

    async function loadVocabulary() {
        loadingEl.classList.remove('hidden');
        errorEl.classList.add('hidden');
        
        try {
            const resp = await fetch('/api/vocabulary');
            const result = await resp.json();
            
            if (result.status === 'success') {
                vocabData.saved = result.data.filter(v => v.status === 'saved');
                vocabData.ignored = result.data.filter(v => v.status === 'ignored');
                
                countSaved.textContent = vocabData.saved.length;
                countIgnored.textContent = vocabData.ignored.length;
                
                tabSaved.innerHTML = '';
                vocabData.saved.forEach((item, index) => {
                    tabSaved.appendChild(createVocabCard(item, index));
                });
                
                tabIgnored.innerHTML = '';
                vocabData.ignored.forEach((item, index) => {
                    tabIgnored.appendChild(createVocabCard(item, index));
                });
                
                if (vocabData.saved.length === 0) {
                    tabSaved.innerHTML = '<div style="color: var(--text-muted); text-align: center; grid-column: 1 / -1; padding: 3rem; background: rgba(255,255,255,0.02); border-radius: 12px; border: 1px dashed rgba(255,255,255,0.1);">尚無儲存的單字，快去解析影片收集吧！✨</div>';
                }
                if (vocabData.ignored.length === 0) {
                    tabIgnored.innerHTML = '<div style="color: var(--text-muted); text-align: center; grid-column: 1 / -1; padding: 3rem; background: rgba(255,255,255,0.02); border-radius: 12px; border: 1px dashed rgba(255,255,255,0.1);">尚無忽略的單字。</div>';
                }
            } else {
                throw new Error(result.message || '載入失敗');
            }
        } catch (e) {
            errorEl.textContent = `錯誤: ${e.message}`;
            errorEl.classList.remove('hidden');
        } finally {
            loadingEl.classList.add('hidden');
        }
    }

    loadVocabulary();
});
