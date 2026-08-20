// BUKA YT Radar — VidIQ-style Dashboard
// Two-column layout: videos left, competitors right

let currentData = {
    monitor: null,
    ideas: null,
    scripts: null
};

let selectedChannels = new Set();
let searchQuery = '';
let competitorSearchQuery = '';
let sortBy = 'views';
let timeRange = 'all';
let videosCurrentPage = 1;
const VIDEOS_PER_PAGE = 15;

const ADMIN_STORAGE_KEY = 'buka_competitors';

// Chart instances
let viewsChartInstance = null;
let timelineChartInstance = null;

// Dropdown labels mapping
const sortLabels = {
    views: 'Просмотры',
    likes: 'Лайки',
    comments: 'Комментарии',
    date: 'Дата'
};

const timeLabels = {
    all: 'Всё время',
    month: 'Этот месяц',
    week: 'Эта неделя',
    '7': 'Последние 7 дней',
    '30': 'Последние 30 дней'
};

// ═══════════════════════════════════════════
// CUSTOM DROPDOWNS
// ═══════════════════════════════════════════

function toggleDropdown(id) {
    const dropdown = document.getElementById(id);
    const isHidden = dropdown.classList.contains('hidden');
    // Close all dropdowns first
    document.querySelectorAll('.dropdown-menu').forEach(d => d.classList.add('hidden'));
    if (isHidden) {
        dropdown.classList.remove('hidden');
    }
}

function closeDropdowns() {
    document.querySelectorAll('.dropdown-menu').forEach(d => d.classList.add('hidden'));
}

// Close dropdowns when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.dropdown-menu') && !e.target.closest('[onclick^="toggleDropdown"]')) {
        closeDropdowns();
    }
});

// ═══════════════════════════════════════════
// ADMIN SYNC
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
// DATA BUILDERS
// ═══════════════════════════════════════════

function buildCompetitorsList() {
    const adminList = getAdminCompetitors().filter(c => c.active !== false);
    const monitorData = currentData.monitor?.data || [];

    const monitorMap = new Map();
    monitorData.forEach(ch => {
        monitorMap.set(ch.channel_id, ch);
    });

    const seen = new Set();
    const result = [];

    adminList.forEach(admin => {
        const id = admin.id;
        seen.add(id);

        const monitored = monitorMap.get(id);
        const enrichedName = monitored?.channel_title || admin.name || id;
        const subs = monitored?.subscriber_count;
        const thumb = monitored?.channel_thumbnail;

        result.push({
            channel_id: id,
            name: enrichedName,
            url: admin.url || `https://www.youtube.com/channel/${id}`,
            subscribers: subs ? formatNumber(subs) : '—',
            subscriber_count: subs || 0,
            thumbnail: thumb || null,
            source: monitored ? 'json' : 'admin'
        });
    });

    monitorData.forEach(ch => {
        if (seen.has(ch.channel_id)) return;
        seen.add(ch.channel_id);

        const channelName = ch.channel_title || ch.channel_id;
        const subs = ch.subscriber_count;
        const thumb = ch.channel_thumbnail;

        result.push({
            channel_id: ch.channel_id,
            name: channelName,
            url: `https://www.youtube.com/channel/${ch.channel_id}`,
            subscribers: subs ? formatNumber(subs) : '—',
            subscriber_count: subs || 0,
            thumbnail: thumb || null,
            source: 'json'
        });
    });

    return result;
}

function getAllVideos() {
    const monitorData = currentData.monitor?.data || [];
    const videos = [];
    monitorData.forEach(ch => {
        (ch.videos || []).forEach(v => {
            videos.push({
                ...v,
                source_channel: ch.channel_title || ch.channel_id,
                source_channel_id: ch.channel_id,
                source_subscribers: ch.subscriber_count || 0,
                source_thumbnail: ch.channel_thumbnail || null
            });
        });
    });
    return videos;
}

function filterVideosByTime(videos) {
    if (timeRange === 'all') return videos;

    const now = new Date();
    const days = parseInt(timeRange);
    if (!days) return videos;

    const cutoff = new Date(now - days * 24 * 60 * 60 * 1000);
    return videos.filter(v => {
        const date = v.published_at ? new Date(v.published_at) : 
                     v.upload_date ? new Date(v.upload_date.slice(0,4), v.upload_date.slice(4,6)-1, v.upload_date.slice(6,8)) : null;
        return date && date >= cutoff;
    });
}

function sortVideos(videos) {
    const sorted = [...videos];
    switch (sortBy) {
        case 'views':
            sorted.sort((a, b) => (b.view_count || 0) - (a.view_count || 0));
            break;
        case 'likes':
            sorted.sort((a, b) => (b.like_count || 0) - (a.like_count || 0));
            break;
        case 'comments':
            sorted.sort((a, b) => (b.comment_count || 0) - (a.comment_count || 0));
            break;
        case 'date':
            sorted.sort((a, b) => {
                const da = a.published_at ? new Date(a.published_at) : new Date(0);
                const db = b.published_at ? new Date(b.published_at) : new Date(0);
                return db - da;
            });
            break;
    }
    return sorted;
}

function searchVideos(query) {
    searchQuery = query;
    videosCurrentPage = 1;
    renderVideos();
}

function changeSort(value) {
    sortBy = value;
    document.getElementById('sortLabel').textContent = sortLabels[value];
    closeDropdowns();
    videosCurrentPage = 1;
    renderVideos();
}

function changeTimeRange(value) {
    timeRange = value;
    document.getElementById('timeLabel').textContent = timeLabels[value];
    closeDropdowns();
    videosCurrentPage = 1;
    renderVideos();
}

function searchCompetitors(query) {
    competitorSearchQuery = query;
    renderCompetitors();
}

// ═══════════════════════════════════════════
// CHARTS
// ═══════════════════════════════════════════

function renderCharts() {
    renderViewsChart();
    renderTimelineChart();
}

function renderViewsChart() {
    const ctx = document.getElementById('viewsChart');
    if (!ctx) return;

    const monitorData = currentData.monitor?.data || [];
    
    // Calculate total_views from videos array since channel object doesn't have total_views field
    const channelsWithViews = monitorData.map(ch => ({
        ...ch,
        total_views: (ch.videos || []).reduce((sum, v) => sum + (v.view_count || 0), 0)
    }));
    
    const sorted = [...channelsWithViews].sort((a, b) => b.total_views - a.total_views).slice(0, 8);

    const labels = sorted.map(ch => ch.channel_title || ch.channel_id);
    const data = sorted.map(ch => ch.total_views);

    if (viewsChartInstance) {
        viewsChartInstance.destroy();
    }

    viewsChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Просмотры',
                data,
                backgroundColor: 'rgba(249, 115, 22, 0.7)',
                borderColor: 'rgba(249, 115, 22, 1)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(48, 54, 61, 0.5)' },
                    ticks: { color: '#8b949e', callback: v => formatNumber(v) }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#8b949e', maxRotation: 45 }
                }
            }
        }
    });
}

function renderTimelineChart() {
    const ctx = document.getElementById('timelineChart');
    if (!ctx) return;

    const videos = getAllVideos();
    const dateMap = new Map();

    videos.forEach(v => {
        const dateStr = v.published_at ? v.published_at.slice(0, 10) : 
                       v.upload_date ? `${v.upload_date.slice(0,4)}-${v.upload_date.slice(4,6)}-${v.upload_date.slice(6,8)}` : null;
        if (!dateStr) return;
        dateMap.set(dateStr, (dateMap.get(dateStr) || 0) + 1);
    });

    const sortedDates = Array.from(dateMap.keys()).sort();
    const last14 = sortedDates.slice(-14);
    const data = last14.map(d => dateMap.get(d));

    if (timelineChartInstance) {
        timelineChartInstance.destroy();
    }

    timelineChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: last14.map(d => d.slice(5)),
            datasets: [{
                label: 'Видео',
                data,
                borderColor: 'rgba(88, 166, 255, 0.8)',
                backgroundColor: 'rgba(88, 166, 255, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: 'rgba(88, 166, 255, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(48, 54, 61, 0.5)' },
                    ticks: { color: '#8b949e', stepSize: 1 }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#8b949e' }
                }
            }
        }
    });
}

// ═══════════════════════════════════════════
// RENDER COMPETITORS (Right Column)
// ═══════════════════════════════════════════

function renderCompetitors() {
    const container = document.getElementById('competitorsList');
    let allCompetitors = buildCompetitorsList();

    // Filter by search
    if (competitorSearchQuery.trim()) {
        const q = competitorSearchQuery.toLowerCase();
        allCompetitors = allCompetitors.filter(c => 
            (c.name || '').toLowerCase().includes(q)
        );
    }

    if (allCompetitors.length === 0) {
        container.innerHTML = '<div class="p-4 text-center text-gray-500 text-sm">Нет конкурентов</div>';
        return;
    }

    // Select all by default on first load
    if (selectedChannels.size === 0) {
        allCompetitors.forEach(c => selectedChannels.add(c.channel_id));
    }

    container.innerHTML = allCompetitors.map(c => {
        const isSelected = selectedChannels.has(c.channel_id);
        const thumbHtml = c.thumbnail
            ? `<img src="${c.thumbnail}" alt="" class="w-8 h-8 rounded-full object-cover" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
            : '';
        const fallbackHtml = `<div class="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-xs font-bold" ${c.thumbnail ? 'style="display:none"' : ''}>${(c.name || '?').charAt(0).toUpperCase()}</div>`;

        return `
            <div class="p-3 flex items-center gap-3 hover:bg-[#21262d] transition cursor-pointer group" onclick="toggleSelect('${c.channel_id}')">
                <input type="checkbox" ${isSelected ? 'checked' : ''} 
                       class="w-4 h-4 rounded border-[#30363d] bg-[#0d1117] text-[#238636] focus:ring-[#238636] cursor-pointer shrink-0"
                       onclick="event.stopPropagation(); toggleSelect('${c.channel_id}')">
                <div class="shrink-0">
                    ${thumbHtml}${fallbackHtml}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="font-medium text-sm truncate group-hover:text-orange-400 transition">${escapeHtml(c.name)}</div>
                    <div class="text-xs text-gray-500">${c.subscribers} подписчиков</div>
                </div>
            </div>
        `;
    }).join('');

    // Update select-all checkbox
    const allCompetitorsFull = buildCompetitorsList();
    const allSelected = allCompetitorsFull.length > 0 && allCompetitorsFull.every(c => selectedChannels.has(c.channel_id));
    document.getElementById('selectAllCheckbox').checked = allSelected;
    document.getElementById('selectedCount').textContent = `${selectedChannels.size} выбрано`;
}

function toggleSelect(channelId) {
    if (selectedChannels.has(channelId)) {
        selectedChannels.delete(channelId);
    } else {
        selectedChannels.add(channelId);
    }
    renderCompetitors();
    renderVideos();
    renderKeywords();
}

function toggleSelectAll() {
    const checkbox = document.getElementById('selectAllCheckbox');
    const allCompetitors = buildCompetitorsList();
    if (checkbox.checked) {
        allCompetitors.forEach(c => selectedChannels.add(c.channel_id));
    } else {
        selectedChannels.clear();
    }
    renderCompetitors();
    renderVideos();
    renderKeywords();
}

// ═══════════════════════════════════════════
// RENDER VIDEOS (Left Column)
// ═══════════════════════════════════════════

function renderVideos() {
    const container = document.getElementById('videosList');
    const paginationContainer = document.getElementById('videosPagination');

    let allVideos = getAllVideos();

    // Filter by selected channels
    allVideos = allVideos.filter(v => selectedChannels.has(v.source_channel_id));

    // Filter by time
    allVideos = filterVideosByTime(allVideos);

    // Filter by search
    if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        allVideos = allVideos.filter(v => 
            (v.title || '').toLowerCase().includes(q) ||
            (v.source_channel || '').toLowerCase().includes(q)
        );
    }

    // Sort
    allVideos = sortVideos(allVideos);

    document.getElementById('videosCount').textContent = `${allVideos.length} видео`;

    if (allVideos.length === 0) {
        container.innerHTML = '<div class="text-center py-10 text-gray-500 text-sm">Нет видео по выбранным фильтрам</div>';
        paginationContainer.innerHTML = '';
        return;
    }

    // Pagination
    const totalPages = Math.ceil(allVideos.length / VIDEOS_PER_PAGE) || 1;
    if (videosCurrentPage > totalPages) videosCurrentPage = totalPages;
    const start = (videosCurrentPage - 1) * VIDEOS_PER_PAGE;
    const pageVideos = allVideos.slice(start, start + VIDEOS_PER_PAGE);

    container.innerHTML = pageVideos.map((v, i) => {
        const globalIndex = start + i + 1;
        const views = v.view_count || 0;
        const likes = v.like_count || 0;
        const dateStr = formatDate(v.published_at || v.upload_date);
        const durationStr = formatDuration(v.duration);

        // Anomaly indicator (simple: top 10% by views)
        const isAnomaly = globalIndex <= 3;

        return `
            <div class="bg-[#161b22] rounded-xl border border-[#30363d] p-3 flex gap-3 hover:border-[#58a6ff] transition group video-card">
                <!-- Thumbnail -->
                <div class="relative shrink-0 w-[160px] h-[90px] rounded-lg overflow-hidden bg-[#0d1117]">
                    ${v.thumbnail ? `<img src="${v.thumbnail}" alt="" class="w-full h-full object-cover" onerror="this.parentElement.innerHTML='<div class=\'w-full h-full flex items-center justify-center text-gray-600\'><i class=\'fas fa-play\'></i></div>'">` : `<div class="w-full h-full flex items-center justify-center text-gray-600"><i class="fas fa-play"></i></div>`}
                    ${durationStr ? `<span class="absolute bottom-1 right-1 bg-black/80 text-white text-[10px] px-1 rounded">${durationStr}</span>` : ''}
                    ${isAnomaly ? `<span class="absolute top-1 left-1 bg-blue-500 text-white text-[10px] w-5 h-5 rounded-full flex items-center justify-center font-bold">${globalIndex}</span>` : ''}
                </div>
                <!-- Info -->
                <div class="flex-1 min-w-0 flex flex-col justify-between py-0.5">
                    <div>
                        <a href="${v.url || '#'}" target="_blank" class="font-medium text-sm text-white hover:text-[#58a6ff] transition line-clamp-2 leading-tight">${escapeHtml(v.title || 'Без названия')}</a>
                        <div class="flex items-center gap-2 mt-1.5">
                            ${v.source_thumbnail ? `<img src="${v.source_thumbnail}" alt="" class="w-4 h-4 rounded-full object-cover" onerror="this.style.display='none'">` : ''}
                            <span class="text-xs text-gray-400">${escapeHtml(v.source_channel || '')}</span>
                            <span class="text-xs text-gray-600">•</span>
                            <span class="text-xs text-gray-500">${formatNumber(v.source_subscribers || 0)} подписчиков</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-4 text-xs text-gray-500 mt-2">
                        <span class="flex items-center gap-1"><i class="fas fa-eye text-gray-600"></i> ${formatNumber(views)}</span>
                        <span class="flex items-center gap-1"><i class="fas fa-thumbs-up text-gray-600"></i> ${formatNumber(likes)}</span>
                        <span>${dateStr}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    renderPagination(paginationContainer, videosCurrentPage, totalPages, allVideos.length);
}

function goToVideosPage(page) {
    videosCurrentPage = page;
    renderVideos();
}

function renderPagination(container, current, total, totalItems) {
    if (total <= VIDEOS_PER_PAGE) {
        container.innerHTML = '';
        return;
    }

    let buttons = '';
    buttons += `<button onclick="goToVideosPage(${current - 1})" ${current === 1 ? 'disabled' : ''} class="px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] disabled:opacity-30 text-xs transition"><i class="fas fa-chevron-left"></i></button>`;

    for (let i = 1; i <= total; i++) {
        if (i === 1 || i === total || (i >= current - 1 && i <= current + 1)) {
            const activeClass = i === current ? 'bg-[#238636] text-white' : 'bg-[#21262d] hover:bg-[#30363d] text-gray-300';
            buttons += `<button onclick="goToVideosPage(${i})" class="px-2.5 py-1 rounded ${activeClass} text-xs transition">${i}</button>`;
        } else if (i === current - 2 || i === current + 2) {
            buttons += `<span class="text-gray-600 text-xs">...</span>`;
        }
    }

    buttons += `<button onclick="goToVideosPage(${current + 1})" ${current === total ? 'disabled' : ''} class="px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] disabled:opacity-30 text-xs transition"><i class="fas fa-chevron-right"></i></button>`;

    container.innerHTML = `
        <div class="flex items-center gap-1">${buttons}</div>
        <span class="text-xs text-gray-500">${current} / ${total} страниц · ${totalItems} всего</span>
    `;
}

// ═══════════════════════════════════════════
// RENDER KEYWORDS & HASHTAGS
// ═══════════════════════════════════════════

function renderKeywords() {
    const kwContainer = document.getElementById('keywordsCloud');
    const htContainer = document.getElementById('hashtagsCloud');

    if (!currentData.ideas || !currentData.ideas.analysis) {
        kwContainer.innerHTML = '<span class="text-xs text-gray-500">Нет данных</span>';
        htContainer.innerHTML = '<span class="text-xs text-gray-500">Нет данных</span>';
        return;
    }

    const analysis = currentData.ideas.analysis;

    // Keywords
    const keywords = analysis.top_keywords || [];
    if (keywords.length > 0) {
        kwContainer.innerHTML = keywords.slice(0, 20).map(([word, score]) => {
            const intensity = Math.min(score / 50, 1);
            const opacity = 0.3 + intensity * 0.7;
            return `<span class="text-xs px-2 py-0.5 rounded-full border border-orange-500/30 bg-orange-500/10 text-orange-400">${word} <span class="text-orange-600">${score}</span></span>`;
        }).join('');
    } else {
        kwContainer.innerHTML = '<span class="text-xs text-gray-500">Нет данных</span>';
    }

    // Hashtags
    const hashtags = analysis.top_hashtags || [];
    if (hashtags.length > 0) {
        htContainer.innerHTML = hashtags.slice(0, 15).map(([tag, count]) => {
            return `<span class="text-xs px-2 py-0.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-400">#${tag} <span class="text-blue-600">${count}</span></span>`;
        }).join('');
    } else {
        htContainer.innerHTML = '<span class="text-xs text-gray-500">Нет данных</span>';
    }
}

// ═══════════════════════════════════════════
// RENDER IDEAS
// ═══════════════════════════════════════════

function renderIdeas() {
    const container = document.getElementById('ideasList');
    const section = document.getElementById('ideasSection');

    if (!currentData.ideas || !currentData.ideas.ideas) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    const ideas = currentData.ideas.ideas;

    const categoryColors = {
        '🔥 Тренд': 'border-red-500/50 bg-red-500/5',
        '🎯 Пробел': 'border-green-500/50 bg-green-500/5',
        '⚡ Горячая': 'border-yellow-500/50 bg-yellow-500/5',
        '💡 Неожиданный': 'border-purple-500/50 bg-purple-500/5',
        '📊 Формат': 'border-blue-500/50 bg-blue-500/5'
    };

    container.innerHTML = ideas.map(idea => {
        const borderClass = categoryColors[idea.category?.split(' ')[0]] || 'border-gray-700 bg-[#161b22]';
        let tagsHtml = '';
        if (idea.recommended_tags && idea.recommended_tags.length > 0) {
            tagsHtml = `<div class="flex flex-wrap gap-1 mt-2">${idea.recommended_tags.slice(0, 4).map(t => `<span class="text-[10px] bg-[#21262d] px-1.5 py-0.5 rounded text-gray-400">${t}</span>`).join('')}</div>`;
        }
        return `
            <div class="bg-[#161b22] rounded-xl border ${borderClass} p-4 hover:border-[#58a6ff]/50 transition">
                <div class="flex items-start justify-between mb-2">
                    <span class="text-[10px] font-bold text-orange-400 uppercase tracking-wide">${idea.category}</span>
                    <span class="text-[10px] text-gray-500">${idea.estimated_difficulty}</span>
                </div>
                <h4 class="font-bold text-sm mb-2 leading-snug">${idea.idea}</h4>
                <p class="text-gray-400 text-xs mb-1"><i class="fas fa-film mr-1 text-gray-600"></i>${idea.format}</p>
                <p class="text-gray-600 text-xs italic">${idea.why_works}</p>
                ${tagsHtml}
            </div>
        `;
    }).join('');
}

// ═══════════════════════════════════════════
// DASHBOARD RENDER
// ═══════════════════════════════════════════

function renderDashboard() {
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');

    const now = new Date().toLocaleString('ru-RU');
    document.getElementById('lastUpdate').textContent = `Обновлено: ${now}`;

    renderCompetitors();
    renderVideos();
    renderKeywords();
    renderIdeas();
    // Delay chart rendering so canvas has proper dimensions after unhiding
    setTimeout(() => renderCharts(), 150);
}

// ═══════════════════════════════════════════
// UTILS
// ═══════════════════════════════════════════

function formatNumber(num) {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    let date;
    if (dateStr.includes('T')) {
        date = new Date(dateStr);
    } else if (dateStr.length === 8) {
        date = new Date(dateStr.slice(0,4), dateStr.slice(4,6)-1, dateStr.slice(6,8));
    } else {
        return dateStr;
    }
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'сегодня';
    if (diffDays === 1) return 'вчера';
    if (diffDays < 7) return `${diffDays} дн. назад`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} нед. назад`;
    return `${Math.floor(diffDays / 30)} мес. назад`;
}

function formatDuration(seconds) {
    if (!seconds) return '';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    if (m >= 60) {
        const h = Math.floor(m / 60);
        const rm = m % 60;
        return `${h}:${rm.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }
    return `${m}:${s.toString().padStart(2, '0')}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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

    if (loaded > 0) {
        renderDashboard();
    }
}

loadDemoData();
