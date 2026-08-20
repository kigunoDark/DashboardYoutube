// BUKA Admin Panel — Competitor Management
// Упрощённая версия: только URL канала

const STORAGE_KEY = 'buka_competitors';

let competitors = [];

// ═══════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════

function init() {
    loadFromStorage();
    renderList();
    updateStats();

    document.getElementById('addForm').addEventListener('submit', handleAdd);
}

// ═══════════════════════════════════════════
// STORAGE
// ═══════════════════════════════════════════

function loadFromStorage() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
            competitors = JSON.parse(raw);
        } else {
            // Default: load from demo data
            competitors = [
                { id: 'UC2UXDak6o7rBm23k3Vv5dww', name: 'Tina Huang', url: 'https://www.youtube.com/channel/UC2UXDak6o7rBm23k3Vv5dww', active: true },
                { id: 'UCwr-evhuzGZgDFrq_1pLt_A', name: 'Error Makes Clever', url: 'https://www.youtube.com/channel/UCwr-evhuzGZgDFrq_1pLt_A', active: true },
            ];
            saveToStorage();
        }
    } catch (e) {
        competitors = [];
    }
}

function saveToStorage() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(competitors));
}

// ═══════════════════════════════════════════
// URL PARSING
// ═══════════════════════════════════════════

function parseYoutubeUrl(url) {
    url = url.trim();

    // /channel/UC...
    let match = url.match(/\/channel\/([a-zA-Z0-9_-]+)/);
    if (match) return { type: 'channel_id', id: match[1], url };

    // /@handle
    match = url.match(/\/@([a-zA-Z0-9_.-]+)/);
    if (match) return { type: 'handle', id: '@' + match[1], url };

    // /c/CustomName
    match = url.match(/\/c\/([a-zA-Z0-9_.-]+)/);
    if (match) return { type: 'custom', id: match[1], url };

    // /user/Username
    match = url.match(/\/user\/([a-zA-Z0-9_-]+)/);
    if (match) return { type: 'user', id: match[1], url };

    return null;
}

// ═══════════════════════════════════════════
// ADD / REMOVE / TOGGLE
// ═══════════════════════════════════════════

function handleAdd(e) {
    e.preventDefault();

    const urlInput = document.getElementById('channelUrl');

    const parsed = parseYoutubeUrl(urlInput.value);
    if (!parsed) {
        alert('Неверный URL YouTube. Поддерживаются форматы:\n/channel/ID\n/@handle\n/c/name');
        return;
    }

    // Check for duplicates
    if (competitors.some(c => c.id === parsed.id)) {
        alert('Этот канал уже в списке!');
        return;
    }

    const newComp = {
        id: parsed.id,
        type: parsed.type,
        name: parsed.id, // placeholder — агенты подтянут реальное название
        url: parsed.url,
        active: true,
        addedAt: new Date().toISOString()
    };

    competitors.push(newComp);
    saveToStorage();
    renderList();
    updateStats();

    // Reset form
    urlInput.value = '';
}

function removeCompetitor(index) {
    if (!confirm('Удалить этого конкурента?')) return;
    competitors.splice(index, 1);
    saveToStorage();
    renderList();
    updateStats();
}

function toggleActive(index) {
    competitors[index].active = !competitors[index].active;
    saveToStorage();
    renderList();
    updateStats();
}

function selectAll(state) {
    competitors.forEach(c => c.active = state);
    saveToStorage();
    renderList();
    updateStats();
}

function clearAll() {
    if (!confirm('Очистить ВЕСЬ список конкурентов?')) return;
    competitors = [];
    saveToStorage();
    renderList();
    updateStats();
}

// ═══════════════════════════════════════════
// RENDER
// ═══════════════════════════════════════════

function renderList() {
    const container = document.getElementById('competitorsList');

    if (competitors.length === 0) {
        container.innerHTML = `
            <div class="p-8 text-center text-gray-500">
                <i class="fas fa-inbox text-4xl mb-3"></i>
                <p>Список пуст. Добавьте первого конкурента слева.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = competitors.map((c, i) => {
        const initial = (c.name || '?').charAt(0).toUpperCase();
        const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500', 'bg-blue-500', 'bg-purple-500', 'bg-pink-500'];
        const colorClass = colors[i % colors.length];

        return `
            <div class="p-4 flex items-center gap-4 hover:bg-gray-750 transition ${!c.active ? 'opacity-50' : ''}">
                <!-- Avatar -->
                <div class="w-12 h-12 ${colorClass} rounded-full flex items-center justify-center text-xl font-bold shrink-0">
                    ${initial}
                </div>

                <!-- Info -->
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                        <span class="font-bold text-lg">${escapeHtml(c.name)}</span>
                        ${c.active ? '<span class="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">Активен</span>' : '<span class="text-xs bg-gray-600 text-gray-400 px-2 py-0.5 rounded">Неактивен</span>'}
                    </div>
                    <a href="${c.url}" target="_blank" class="text-sm text-orange-400 hover:underline truncate block">${c.url}</a>
                </div>

                <!-- Actions -->
                <div class="flex items-center gap-2 shrink-0">
                    <button onclick="toggleActive(${i})" title="${c.active ? 'Деактивировать' : 'Активировать'}"
                            class="w-10 h-10 rounded-lg ${c.active ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'} transition flex items-center justify-center">
                        <i class="fas ${c.active ? 'fa-check' : 'fa-times'}"></i>
                    </button>
                    <button onclick="removeCompetitor(${i})" title="Удалить"
                            class="w-10 h-10 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition flex items-center justify-center">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function updateStats() {
    document.getElementById('totalCompetitors').textContent = competitors.length;
    document.getElementById('activeCompetitors').textContent = competitors.filter(c => c.active).length;
    document.getElementById('inactiveCompetitors').textContent = competitors.filter(c => !c.active).length;
}

// ═══════════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════════

function exportToConfig() {
    const config = {
        youtube_api_key: "",
        use_youtube_api: false,
        telegram_bot_token: "",
        telegram_chat_id: "",
        enable_telegram: false,
        competitors: competitors.filter(c => c.active).map(c => ({
            channel_id: c.id
        })),
        settings: {
            videos_per_competitor: 10,
            top_videos_to_analyze: 10,
            monitor_interval_days: 2,
            language: "ru",
            niche_keywords: [
                "IT карьера", "программист", "релокация", "зарплата в IT",
                "junior developer", "Staff инженер", "AI замена программистов",
                "собеседование IT", "рынок труда IT", "миграция программист"
            ]
        }
    };

    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'config.json';
    link.click();
}

function exportToCSV() {
    let csv = 'ID,Name,URL,Active\n';
    competitors.forEach(c => {
        csv += `"${c.id}","${c.name}","${c.url}",${c.active ? 'yes' : 'no'}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `competitors_${new Date().toISOString().slice(0,10)}.csv`;
    link.click();
}

// ═══════════════════════════════════════════
// UTILS
// ═══════════════════════════════════════════

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ═══════════════════════════════════════════
// START
// ═══════════════════════════════════════════

init();
