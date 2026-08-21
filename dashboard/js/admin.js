// BUKA Admin Panel — Competitor Management
// Упрощённая версия: только URL канала + поиск + пагинация

const STORAGE_KEY = 'buka_competitors';

let competitors = [];
let adminSearchQuery = '';
let adminCurrentPage = 1;
const ADMIN_ITEMS_PER_PAGE = 10;

// ═══════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════

function init() {
    loadFromStorage();

    // Если локальный список пуст — подтягиваем каналы из свежего monitor-отчёта,
    // чтобы админка показывала тех же конкурентов, что и главная страница.
    if (competitors.length === 0) {
        seedFromMonitorReport().then(() => {
            renderList();
            updateStats();
        });
    } else {
        renderList();
        updateStats();
    }

    document.getElementById('addForm').addEventListener('submit', handleAdd);
}

// ═══════════════════════════════════════════
// SEED FROM MONITOR REPORT
// ═══════════════════════════════════════════

async function seedFromMonitorReport() {
    try {
        const res = await fetch('data/monitor_report_latest.json');
        if (!res.ok) return false;
        const data = await res.json();
        const channels = (data.data || [])
            .filter(ch => ch.channel_id)
            .map(ch => ({
                id: ch.channel_id,
                name: ch.channel_title || ch.channel_id,
                url: `https://www.youtube.com/channel/${ch.channel_id}`,
                active: true
            }));
        if (channels.length === 0) return false;
        competitors = channels;
        saveToStorage();
        return true;
    } catch (e) {
        console.error('Seed from monitor report failed:', e);
        return false;
    }
}

async function reimportFromReport() {
    if (!confirm('Заменить текущий список каналами из свежего отчёта?')) return;
    const ok = await seedFromMonitorReport();
    if (!ok) alert('Не удалось загрузить monitor_report_latest.json');
    renderList();
    updateStats();
}

// ═══════════════════════════════════════════
// STORAGE
// ═══════════════════════════════════════════

function loadFromStorage() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
            const parsed = JSON.parse(raw);
            competitors = Array.isArray(parsed) ? parsed : [];
        } else {
            // Пусто — init() подтянет каналы из monitor-отчёта
            competitors = [];
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
    adminCurrentPage = 1; // reset to first page
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
// SEARCH & PAGINATION
// ═══════════════════════════════════════════

function searchAdminCompetitors(query) {
    adminSearchQuery = query;
    adminCurrentPage = 1;
    renderList();
}

function getFilteredCompetitors() {
    let list = competitors;
    if (adminSearchQuery.trim()) {
        const q = adminSearchQuery.toLowerCase();
        list = competitors.filter(c =>
            (c.name || '').toLowerCase().includes(q) ||
            (c.url || '').toLowerCase().includes(q) ||
            (c.id || '').toLowerCase().includes(q)
        );
    }
    return list;
}

function goToAdminPage(page) {
    const filtered = getFilteredCompetitors();
    const totalPages = Math.ceil(filtered.length / ADMIN_ITEMS_PER_PAGE) || 1;
    if (page < 1) page = 1;
    if (page > totalPages) page = totalPages;
    adminCurrentPage = page;
    renderList();
}

// ═══════════════════════════════════════════
// RENDER
// ═══════════════════════════════════════════

function renderList() {
    const container = document.getElementById('competitorsList');
    const paginationContainer = document.getElementById('adminPagination');
    const filtered = getFilteredCompetitors();

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="p-8 text-center text-gray-500">
                <i class="fas fa-inbox text-4xl mb-3"></i>
                <p>Ничего не найдено. Добавьте первого конкурента или измените поиск.</p>
            </div>
        `;
        paginationContainer.innerHTML = '';
        return;
    }

    const totalPages = Math.ceil(filtered.length / ADMIN_ITEMS_PER_PAGE) || 1;
    const start = (adminCurrentPage - 1) * ADMIN_ITEMS_PER_PAGE;
    const pageItems = filtered.slice(start, start + ADMIN_ITEMS_PER_PAGE);

    container.innerHTML = pageItems.map((c, i) => {
        const realIndex = competitors.indexOf(c);
        const initial = (c.name || '?').charAt(0).toUpperCase();
        const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500', 'bg-blue-500', 'bg-purple-500', 'bg-pink-500'];
        const colorClass = colors[realIndex % colors.length];

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
                    <button onclick="toggleActive(${realIndex})" title="${c.active ? 'Деактивировать' : 'Активировать'}"
                            class="w-10 h-10 rounded-lg ${c.active ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'} transition flex items-center justify-center">
                        <i class="fas ${c.active ? 'fa-check' : 'fa-times'}"></i>
                    </button>
                    <button onclick="removeCompetitor(${realIndex})" title="Удалить"
                            class="w-10 h-10 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition flex items-center justify-center">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    // Render pagination
    renderPagination(paginationContainer, adminCurrentPage, totalPages, filtered.length);
}

function renderPagination(container, current, total, totalItems) {
    if (total <= 1) {
        container.innerHTML = `<span class="text-sm text-gray-500">${totalItems} конкурентов</span>`;
        return;
    }

    let buttons = '';
    // Prev
    buttons += `<button onclick="goToAdminPage(${current - 1})" ${current === 1 ? 'disabled' : ''} class="px-3 py-1 rounded bg-gray-700 hover:bg-gray-600 disabled:opacity-30 disabled:cursor-not-allowed text-sm transition"><i class="fas fa-chevron-left"></i></button>`;

    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, current - Math.floor(maxVisible / 2));
    let endPage = Math.min(total, startPage + maxVisible - 1);
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
        buttons += `<button onclick="goToAdminPage(1)" class="px-3 py-1 rounded bg-gray-700 hover:bg-gray-600 text-sm transition">1</button>`;
        if (startPage > 2) buttons += `<span class="px-2 text-gray-500">...</span>`;
    }

    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === current ? 'bg-orange-500 text-white' : 'bg-gray-700 hover:bg-gray-600';
        buttons += `<button onclick="goToAdminPage(${i})" class="px-3 py-1 rounded ${activeClass} text-sm transition">${i}</button>`;
    }

    if (endPage < total) {
        if (endPage < total - 1) buttons += `<span class="px-2 text-gray-500">...</span>`;
        buttons += `<button onclick="goToAdminPage(${total})" class="px-3 py-1 rounded bg-gray-700 hover:bg-gray-600 text-sm transition">${total}</button>`;
    }

    // Next
    buttons += `<button onclick="goToAdminPage(${current + 1})" ${current === total ? 'disabled' : ''} class="px-3 py-1 rounded bg-gray-700 hover:bg-gray-600 disabled:opacity-30 disabled:cursor-not-allowed text-sm transition"><i class="fas fa-chevron-right"></i></button>`;

    container.innerHTML = `
        <div class="flex items-center gap-2">
            ${buttons}
        </div>
        <span class="text-sm text-gray-500">Страница ${current} из ${total} · ${totalItems} всего</span>
    `;
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
