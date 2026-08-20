// BUKA YouTube System Dashboard v2
// Competitor selector + filtered analytics
// Теперь синхронизирован с localStorage админки!

let currentData = {
    monitor: null,
    ideas: null,
    scripts: null
};

let selectedChannels = new Set();   // channel_ids that are checked
let searchQuery = '';               // current search text
let viewsChartInstance = null;
let allCompetitorsList = [];        // cached list for search

const ADMIN_STORAGE_KEY = 'buka_competitors';

// ═══════════════════════════════════════════
// ADMIN SYNC — читаем конкурентов из админки
// ═══════════════════════════════════════════

function getAdminCompetitors() {
    try {
        const raw = localStorage.getItem(ADMIN_STORAGE_KEY);
        if (raw) return JSON.parse(raw);
    } catch (e) {
        console.error('Error reading admin competitors:', e);
    }
    return [];
}

// ═══════════════════════════════════════════
// FILE HANDLING
// ═══════════════════════════════════════════

function handleFiles(event) {
    const files = event.target.files || event.dataTransfer.files;
    if (!files.length) return;

    let loaded = 0;
    const total = files.length;

    Array.from(files).forEach(file => {
        if (!file.name.endsWith('.json')) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                categorizeFile(file.name, data);
                loaded++;
                if (loaded === total) renderDashboard();
            } catch (err) {
                console.error('Error parsing', file.name, err);
            }
        };
        reader.readAsText(file);
    });
}

function categorizeFile(filename, data) {
    if (filename.includes('monitor_report')) {
        currentData.monitor = data;
    } else if (filename.includes('ideas_report')) {
        currentData.ideas = data;
    } else if (filename.includes('scripts_index') || filename.includes('pipeline_report')) {
        currentData.scripts = data;
    }
}

// ═══════════════════════════════════════════
// COMPETITOR SELECTOR
// ═══════════════════════════════════════════

function buildCompetitorsList() {
    const adminList = getAdminCompetitors().filter(c => c.active !== false);
    const monitorData = currentData.monitor?.data || [];

    // Map monitor data by channel_id for quick lookup
    const monitorMap = new Map();
    monitorData.forEach(ch => {
        monitorMap.set(ch.channel_id, ch);
    });

    // Build unified list: admin competitors + monitor data merged
    const seen = new Set();
    const result = [];

    // 1. Start with admin competitors (from localStorage)
    adminList.forEach(admin => {
        const id = admin.id;
        seen.add(id);

        // Try to find enriched data from monitor JSON
        const monitored = monitorMap.get(id);
        const firstVideo = monitored?.videos?.[0];
        const enrichedName = firstVideo?.channel || monitored?.channel_id || admin.name || id;
        const lastVideo = monitored?.videos?.[0];

        result.push({
            channel_id: id,
            name: enrichedName,
            url: admin.url || `https://www.youtube.com/channel/${id}`,
            subscribers: '—', // would need API
            lastVideoTitle: lastVideo?.title || '—',
            lastVideoUrl: lastVideo?.url || '#',
            avatarInitial: (enrichedName || '?').charAt(0).toUpperCase(),
            avatarColor: stringToColor(id),
            source: monitored ? 'json' : 'admin'
        });
    });

    // 2. Add any monitor channels not in admin list (legacy / uploaded JSON)
    monitorData.forEach(ch => {
        if (seen.has(ch.channel_id)) return;
        seen.add(ch.channel_id);

        const firstVideo = ch.videos?.[0];
        const channelName = firstVideo?.channel || ch.channel_id;
        const lastVideo = ch.videos?.[0];

        result.push({
            channel_id: ch.channel_id,
            name: channelName,
            url: `https://www.youtube.com/channel/${ch.channel_id}`,
            subscribers: '—',
            lastVideoTitle: lastVideo?.title || '—',
            lastVideoUrl: lastVideo?.url || '#',
            avatarInitial: (channelName || '?').charAt(0).toUpperCase(),
            avatarColor: stringToColor(ch.channel_id),
            source: 'json'
        });
    });

    return result;
}

function stringToColor(str) {
    const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500', 'bg-blue-500', 'bg-purple-500', 'bg-pink-500', 'bg-indigo-500', 'bg-teal-500', 'bg-cyan-500'];
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
    return colors[Math.abs(hash) % colors.length];
}

function renderCompetitorsSelector() {
    const tbody = document.getElementById('competitorsSelectorBody');
    tbody.innerHTML = '';

    allCompetitorsList = buildCompetitorsList();
    let filtered = allCompetitorsList;

    if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        filtered = allCompetitorsList.filter(c => c.name.toLowerCase().includes(q));
    }

    // Update select-all checkbox state
    const allSelected = allCompetitorsList.length > 0 && allCompetitorsList.every(c => selectedChannels.has(c.channel_id));
    document.getElementById('selectAllCheckbox').checked = allSelected;
    document.getElementById('selectedCount').textContent = `(${selectedChannels.size} выбрано)`;

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-500">Нет конкурентов. Добавьте их в <a href="admin.html" class="text-orange-400 underline">админке</a> или загрузите JSON.</td></tr>';
        return;
    }

    filtered.forEach(c => {
        const isSelected = selectedChannels.has(c.channel_id);
        const sourceBadge = c.source === 'json'
            ? '<span class="ml-2 text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">JSON</span>'
            : '<span class="ml-2 text-[10px] bg-gray-600/50 text-gray-400 px-1.5 py-0.5 rounded">admin</span>';

        const row = document.createElement('tr');
        row.className = `border-b border-gray-700/50 hover:bg-gray-700/30 transition ${isSelected ? 'bg-orange-500/5' : ''}`;
        row.innerHTML = `
            <td class="p-3">
                <input type="checkbox" ${isSelected ? 'checked' : ''} onchange="toggleSelect('${c.channel_id}')"
                       class="w-5 h-5 rounded border-gray-600 text-orange-500 focus:ring-orange-500 cursor-pointer">
            </td>
            <td class="p-3">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 ${c.avatarColor} rounded-full flex items-center justify-center text-sm font-bold shrink-0">
                        ${c.avatarInitial}
                    </div>
                    <span class="font-medium">${escapeHtml(c.name)}</span>
                    ${sourceBadge}
                </div>
            </td>
            <td class="p-3 text-gray-400">${c.subscribers}</td>
            <td class="p-3">
                <a href="${c.lastVideoUrl}" target="_blank" class="text-orange-400 hover:underline text-sm line-clamp-1">${escapeHtml(c.lastVideoTitle)}</a>
            </td>
            <td class="p-3">
                <a href="${c.url}" target="_blank" class="text-gray-400 hover:text-white text-sm"><i class="fas fa-external-link-alt mr-1"></i>Канал</a>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function toggleSelect(channelId) {
    if (selectedChannels.has(channelId)) {
        selectedChannels.delete(channelId);
    } else {
        selectedChannels.add(channelId);
    }
    renderCompetitorsSelector();
    renderAnalytics();
}

function toggleSelectAll() {
    const checkbox = document.getElementById('selectAllCheckbox');
    if (checkbox.checked) {
        allCompetitorsList.forEach(c => selectedChannels.add(c.channel_id));
    } else {
        selectedChannels.clear();
    }
    renderCompetitorsSelector();
    renderAnalytics();
}

function searchCompetitors(query) {
    searchQuery = query;
    renderCompetitorsSelector();
}

// ═══════════════════════════════════════════
// FILTERED DATA
// ═══════════════════════════════════════════

function getFilteredChannels() {
    const monitorData = currentData.monitor?.data || [];
    if (selectedChannels.size === 0) return [];

    // Return monitor data for selected channels
    const filtered = monitorData.filter(ch => selectedChannels.has(ch.channel_id));

    // If some selected channels have no monitor data yet, return placeholder objects
    // so the table doesn't break
    const adminIds = getAdminCompetitors().filter(c => c.active !== false).map(c => c.id);
    const monitorIds = new Set(monitorData.map(ch => ch.channel_id));

    adminIds.forEach(id => {
        if (selectedChannels.has(id) && !monitorIds.has(id)) {
            filtered.push({
                channel_id: id,
                videos: [],
                _placeholder: true
            });
        }
    });

    return filtered;
}

// ═══════════════════════════════════════════
// RENDER DASHBOARD
// ═══════════════════════════════════════════

function renderDashboard() {
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
    document.getElementById('dashboard').classList.add('animate-fade-in');

    const now = new Date().toLocaleString('ru-RU');
    document.getElementById('lastUpdate').textContent = `Обновлено: ${now}`;

    // Select all by default on first load (only if nothing selected yet)
    if (selectedChannels.size === 0 && allCompetitorsList.length > 0) {
        allCompetitorsList.forEach(c => selectedChannels.add(c.channel_id));
    }

    renderCompetitorsSelector();
    renderAnalytics();
}

function renderAnalytics() {
    renderStats();
    renderVideosTable();
    renderCharts();
    renderKeywords();
    renderIdeas();
    renderScripts();
}

// ═══════════════════════════════════════════
// STATS
// ═══════════════════════════════════════════

function renderStats() {
    const filteredChannels = getFilteredChannels();
    let videos = 0, ideas = 0, avgViews = 0;

    let totalViews = 0;
    let count = 0;
    filteredChannels.forEach(ch => {
        (ch.videos || []).forEach(v => {
            if (v.view_count) {
                totalViews += v.view_count;
                count++;
            }
        });
    });
    videos = count;
    avgViews = count > 0 ? Math.round(totalViews / count) : 0;

    if (currentData.ideas) {
        ideas = (currentData.ideas.ideas || []).length;
    }

    document.getElementById('statChannels').textContent = filteredChannels.length;
    document.getElementById('statVideos').textContent = videos;
    document.getElementById('statIdeas').textContent = ideas;
    document.getElementById('statAvgViews').textContent = formatNumber(avgViews);
}

// ═══════════════════════════════════════════
// VIDEOS TABLE
// ═══════════════════════════════════════════

function renderVideosTable() {
    const tbody = document.getElementById('videosTableBody');
    tbody.innerHTML = '';

    const filteredChannels = getFilteredChannels();
    if (!filteredChannels.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-gray-500">Выберите конкурентов выше</td></tr>';
        return;
    }

    const allVideos = [];
    filteredChannels.forEach(ch => {
        (ch.videos || []).forEach(v => {
            allVideos.push({
                channel: v.channel || ch.channel_id,
                title: v.title || 'N/A',
                views: v.view_count || 0,
                likes: v.like_count || 0,
                comments: v.comment_count || 0,
                date: v.upload_date || '',
                url: v.url || '#'
            });
        });
    });

    if (allVideos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-gray-500">Нет данных о видео. Запустите агентов для сбора.</td></tr>';
        return;
    }

    allVideos.sort((a, b) => b.views - a.views);

    allVideos.forEach(v => {
        const er = v.views > 0 ? ((v.likes + v.comments * 2) / v.views * 100).toFixed(2) : '0';
        const dateStr = v.date ? `${v.date.slice(0,4)}-${v.date.slice(4,6)}-${v.date.slice(6,8)}` : '';

        const row = document.createElement('tr');
        row.className = 'border-b border-gray-700';
        row.innerHTML = `
            <td class="p-3 text-gray-300">${v.channel.slice(0, 20)}...</td>
            <td class="p-3">
                <a href="${v.url}" target="_blank" class="text-orange-400 hover:text-orange-300 hover:underline line-clamp-2">${v.title}</a>
            </td>
            <td class="p-3 text-right font-mono">${formatNumber(v.views)}</td>
            <td class="p-3 text-right font-mono text-green-400">${formatNumber(v.likes)}</td>
            <td class="p-3 text-right font-mono">${er}%</td>
            <td class="p-3 text-gray-400">${dateStr}</td>
        `;
        tbody.appendChild(row);
    });
}

// ═══════════════════════════════════════════
// CHARTS
// ═══════════════════════════════════════════

function renderCharts() {
    if (!currentData.monitor) return;

    const filteredChannels = getFilteredChannels();
    const allVideos = [];
    filteredChannels.forEach(ch => {
        (ch.videos || []).forEach(v => {
            if (v.view_count) {
                allVideos.push({
                    title: v.title?.slice(0, 25) + '...' || 'N/A',
                    views: v.view_count
                });
            }
        });
    });

    if (allVideos.length === 0) return;

    allVideos.sort((a, b) => b.views - a.views);
    const top10 = allVideos.slice(0, 10).reverse();

    const ctx = document.getElementById('viewsChart').getContext('2d');

    if (viewsChartInstance) viewsChartInstance.destroy();

    viewsChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(v => v.title),
            datasets: [{
                label: 'Просмотры',
                data: top10.map(v => v.views),
                backgroundColor: 'rgba(249, 115, 22, 0.8)',
                borderColor: '#f97316',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { color: '#374151' } },
                y: { ticks: { color: '#9ca3af', font: { size: 10 } }, grid: { display: false } }
            }
        }
    });
}

// ═══════════════════════════════════════════
// KEYWORDS
// ═══════════════════════════════════════════

function renderKeywords() {
    const container = document.getElementById('keywordsCloud');
    container.innerHTML = '';

    if (!currentData.ideas || !currentData.ideas.analysis) return;

    const keywords = currentData.ideas.analysis.top_keywords || [];
    keywords.forEach(([word, count]) => {
        const tag = document.createElement('span');
        tag.className = 'keyword-tag';
        tag.textContent = `${word} (${count})`;
        container.appendChild(tag);
    });
}

// ═══════════════════════════════════════════
// IDEAS
// ═══════════════════════════════════════════

function renderIdeas() {
    const container = document.getElementById('ideasList');
    container.innerHTML = '';

    if (!currentData.ideas || !currentData.ideas.ideas) return;

    const categoryColors = {
        '🔥 Тренд': 'border-red-500',
        '🎯 Пробел': 'border-green-500',
        '⚡ Горячая': 'border-yellow-500',
        '💡 Неожиданный': 'border-purple-500',
        '📊 Формат': 'border-blue-500'
    };

    currentData.ideas.ideas.forEach(idea => {
        const card = document.createElement('div');
        card.className = `idea-card bg-gray-700 rounded-lg p-4 ${categoryColors[idea.category?.split(' ')[0]] || 'border-orange-500'}`;
        card.innerHTML = `
            <div class="flex items-start justify-between mb-2">
                <span class="text-xs font-bold text-orange-400 uppercase tracking-wide">${idea.category}</span>
                <span class="text-xs text-gray-400">${idea.estimated_difficulty}</span>
            </div>
            <h4 class="font-bold text-lg mb-2">${idea.idea}</h4>
            <p class="text-gray-400 text-sm mb-2"><i class="fas fa-film mr-1"></i> ${idea.format}</p>
            <p class="text-gray-500 text-sm italic">${idea.why_works}</p>
        `;
        container.appendChild(card);
    });
}

// ═══════════════════════════════════════════
// SCRIPTS
// ═══════════════════════════════════════════

function renderScripts() {
    const container = document.getElementById('scriptsList');
    container.innerHTML = '';

    if (!currentData.scripts || !currentData.scripts.generated_scripts) {
        container.innerHTML = '<p class="text-gray-500">Нет данных о сценариях. Загрузите scripts_index файл.</p>';
        return;
    }

    currentData.scripts.generated_scripts.forEach((script) => {
        const item = document.createElement('div');
        item.className = 'bg-gray-700 rounded-lg p-4 flex items-center justify-between';
        item.innerHTML = `
            <div>
                <span class="text-orange-400 font-bold mr-2">#${script.idea_id}</span>
                <span class="text-white">${script.idea}</span>
            </div>
            <div class="flex gap-2">
                <span class="text-xs bg-gray-600 px-2 py-1 rounded text-gray-300">prompt</span>
                <span class="text-xs bg-gray-600 px-2 py-1 rounded text-gray-300">template</span>
            </div>
        `;
        container.appendChild(item);
    });
}

// ═══════════════════════════════════════════
// UTILS
// ═══════════════════════════════════════════

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function exportTable() {
    const filteredChannels = getFilteredChannels();
    let csv = 'Channel,Title,Views,Likes,Comments,URL\n';
    filteredChannels.forEach(ch => {
        (ch.videos || []).forEach(v => {
            csv += `"${ch.channel_id}","${(v.title || '').replace(/"/g, '\\"')}",${v.view_count || 0},${v.like_count || 0},${v.comment_count || 0},"${v.url || ''}"\n`;
        });
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `competitors_${new Date().toISOString().slice(0,10)}.csv`;
    link.click();
}

// ═══════════════════════════════════════════
// DRAG & DROP
// ═══════════════════════════════════════════

const dropZone = document.body;

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    handleFiles(e);
});

// ═══════════════════════════════════════════
// AUTO-LOAD DEMO DATA
// ═══════════════════════════════════════════

async function loadDemoData() {
    const files = [
        { name: 'monitor_report_2026-08-20.json', url: 'data/monitor_report_2026-08-20.json' },
        { name: 'ideas_report_2026-08-20.json', url: 'data/ideas_report_2026-08-20.json' },
        { name: 'scripts_index_2026-08-20.json', url: 'data/scripts_index_2026-08-20.json' }
    ];

    let loaded = 0;
    for (const f of files) {
        try {
            const response = await fetch(f.url);
            if (!response.ok) continue;
            const data = await response.json();
            categorizeFile(f.name, data);
            loaded++;
        } catch (e) {
            console.log('Demo data not found:', f.url);
        }
    }

    // Always render dashboard — even without JSON data,
    // because admin competitors are stored in localStorage
    renderDashboard();
}

loadDemoData();
