// BUKA YT Radar — Golden Topics v1
// Скоринг тем-аутлаеров: множитель от медианы канала + скорость набора.
// Работает на клиенте из monitor_report (getAllVideos() из app.js).

function median(arr) {
    if (!arr.length) return 0;
    const s = [...arr].sort((a, b) => a - b);
    const m = Math.floor(s.length / 2);
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function getVideoDate(v) {
    if (v.published_at) return new Date(v.published_at);
    if (v.upload_date && v.upload_date.length === 8) {
        return new Date(v.upload_date.slice(0, 4), v.upload_date.slice(4, 6) - 1, v.upload_date.slice(6, 8));
    }
    return null;
}

// Пороги решения
const GOLDEN_MIN_MULTIPLIER = 3;   // минимум 3× от медианы канала
const GOLDEN_FRESH_DAYS = 30;      // моложе 30 дней — тренд ещё открыт
const GOLDEN_MIN_VELOCITY = 1000;  // или быстрее 1000 просмотров/день

function computeGoldenTopics(videos) {
    // Группируем по каналу → медиана просмотров канала
    const byChannel = {};
    for (const v of videos) {
        const cid = v.source_channel_id || 'unknown';
        (byChannel[cid] ??= []).push(v.view_count || 0);
    }
    const medians = Object.fromEntries(
        Object.entries(byChannel).map(([c, views]) => [c, median(views)])
    );

    return videos
        .map(v => {
            const views = v.view_count || 0;
            const med = medians[v.source_channel_id] || 1;
            const date = getVideoDate(v);
            const ageDays = date ? (Date.now() - date.getTime()) / 864e5 : 365;
            const multiplier = med > 0 ? views / med : 0;
            const velocity = views / Math.max(ageDays, 1);
            return {
                title: v.title || 'Без названия',
                url: v.url || '#',
                channel: v.source_channel || '',
                channel_id: v.source_channel_id,
                thumbnail: v.thumbnail || null,
                views,
                multiplier,
                velocity,
                ageDays: Math.round(ageDays),
                // Правило: в контент-план, если ≥3× и (свежее или быстро набирает)
                actionable: multiplier >= GOLDEN_MIN_MULTIPLIER &&
                            (ageDays < GOLDEN_FRESH_DAYS || velocity > GOLDEN_MIN_VELOCITY)
            };
        })
        .filter(t => t.multiplier >= GOLDEN_MIN_MULTIPLIER)
        .sort((a, b) => b.multiplier - a.multiplier);
}

function renderGoldenTopics() {
    const section = document.getElementById('goldenSection');
    const container = document.getElementById('goldenList');
    if (!section || !container) return;

    if (!currentData.monitor || !currentData.monitor.data) {
        section.classList.add('hidden');
        return;
    }

    const topics = computeGoldenTopics(getAllVideos());
    if (topics.length === 0) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');

    container.innerHTML = topics.map(t => {
        // Цветовая шкала множителя: ≥10× янтарный, 3–10× синий
        const multBadge = t.multiplier >= 10
            ? 'bg-amber-500/20 text-amber-400 border-amber-500/40'
            : 'bg-blue-500/20 text-blue-400 border-blue-500/40';

        // Возраст: < 30 дней — тренд открыт (зелёный), > 180 — вечнозелёное (серый)
        const ageBadge = t.ageDays < GOLDEN_FRESH_DAYS
            ? 'bg-green-500/20 text-green-400 border-green-500/40'
            : t.ageDays > 180
                ? 'bg-gray-600/40 text-gray-400 border-gray-600'
                : 'bg-[#21262d] text-gray-400 border-[#30363d]';

        const actionBadge = t.actionable
            ? '<span class="text-[10px] font-bold text-orange-400 uppercase tracking-wide shrink-0">🎬 Снимать</span>'
            : '';

        return `
            <div class="bg-[#161b22] rounded-xl border border-[#30363d] p-3 flex items-center gap-3 hover:border-[#58a6ff] transition">
                <span class="px-2 py-1 rounded-lg border text-sm font-bold shrink-0 ${multBadge}"
                      title="Просмотры / медиана канала">${t.multiplier.toFixed(1)}×</span>
                <div class="flex-1 min-w-0">
                    <a href="${t.url}" target="_blank" class="font-medium text-sm text-white hover:text-[#58a6ff] transition line-clamp-1">${escapeHtml(t.title)}</a>
                    <div class="text-xs text-gray-500 mt-0.5">
                        ${escapeHtml(t.channel)} · ${formatNumber(t.views)} просмотров ·
                        ${Math.round(t.velocity)}/день
                    </div>
                </div>
                <span class="px-2 py-0.5 rounded-full border text-[10px] shrink-0 ${ageBadge}">${t.ageDays} дн.</span>
                ${actionBadge}
            </div>
        `;
    }).join('');

    const actionableCount = topics.filter(t => t.actionable).length;
    const counter = document.getElementById('goldenCount');
    if (counter) {
        counter.textContent = `${topics.length} тем · ${actionableCount} в контент-план`;
    }
}
