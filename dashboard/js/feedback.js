const MY_VIDEOS_STORAGE_KEY = 'buka_my_videos_v1';
const MIN_PACKAGE_CTR = 4;
const MIN_RETENTION = 35;

let myVideos = [];

function $(id) {
    return document.getElementById(id);
}

function isFiniteNumber(value) {
    return typeof value === 'number' && Number.isFinite(value);
}

function readOptionalNumber(id) {
    const value = $(id).value.trim();
    if (value === '') return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
}

function newId() {
    if (window.crypto?.randomUUID) return window.crypto.randomUUID();
    return `video_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function isSafeUrl(value) {
    try {
        const url = new URL(value);
        return url.protocol === 'https:' || url.protocol === 'http:';
    } catch (error) {
        return false;
    }
}

function escapeHtml(value) {
    const node = document.createElement('div');
    node.textContent = value ?? '';
    return node.innerHTML;
}

function formatNumber(value) {
    return new Intl.NumberFormat('ru-RU').format(value);
}

function formatDecimal(value) {
    return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 }).format(value);
}

function formatDate(value) {
    if (!value) return '—';
    const date = new Date(`${value}T12:00:00`);
    if (Number.isNaN(date.getTime())) return '—';
    return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium' }).format(date);
}

function showStatus(message, type = 'success') {
    const status = $('feedbackStatus');
    status.textContent = message;
    status.className = type === 'error'
        ? 'mb-5 rounded-lg border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-100'
        : 'mb-5 rounded-lg border border-emerald-800 bg-emerald-950/40 px-4 py-3 text-sm text-emerald-100';
}

function loadVideos() {
    try {
        const raw = localStorage.getItem(MY_VIDEOS_STORAGE_KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        const videos = Array.isArray(parsed) ? parsed : parsed.videos;
        return Array.isArray(videos) ? videos.map(normalizeVideo).filter(Boolean) : [];
    } catch (error) {
        showStatus('Не удалось прочитать сохранённые результаты. Импортируй резервную копию, если она есть.', 'error');
        return [];
    }
}

function saveVideos() {
    localStorage.setItem(MY_VIDEOS_STORAGE_KEY, JSON.stringify(myVideos));
}

function normalizeVideo(video) {
    if (!video || typeof video !== 'object') return null;
    const expectedMultiplier = Number(video.expectedMultiplier);
    const baselineViews = Number(video.baselineViews);
    const title = String(video.title || '').trim();
    const url = String(video.url || '').trim();
    const topic = String(video.topic || '').trim();
    const publishedAt = String(video.publishedAt || '');

    if (!title || !topic || !publishedAt || !isSafeUrl(url) || expectedMultiplier <= 0 || baselineViews <= 0) {
        return null;
    }

    const numberOrNull = value => {
        if (value === null || value === undefined || value === '') return null;
        const number = Number(value);
        return Number.isFinite(number) && number >= 0 ? number : null;
    };
    const suppliedId = String(video.id || '');

    return {
        id: /^[a-zA-Z0-9_-]+$/.test(suppliedId) ? suppliedId : newId().replace(/-/g, '_'),
        title,
        url,
        topic,
        publishedAt,
        expectedMultiplier,
        baselineViews,
        views24h: numberOrNull(video.views24h),
        views7d: numberOrNull(video.views7d),
        views30d: numberOrNull(video.views30d),
        impressions: numberOrNull(video.impressions),
        ctr: numberOrNull(video.ctr),
        averageViewedPercent: numberOrNull(video.averageViewedPercent),
        createdAt: video.createdAt || new Date().toISOString(),
        updatedAt: video.updatedAt || new Date().toISOString()
    };
}

function actualMultiplier(video) {
    if (!isFiniteNumber(video.views7d) || !isFiniteNumber(video.baselineViews) || video.baselineViews <= 0) {
        return null;
    }
    return video.views7d / video.baselineViews;
}

function getSignal(video) {
    const actual = actualMultiplier(video);
    if (actual === null) {
        return {
            tone: 'gray',
            label: 'Ждём 7 дней',
            description: 'Добавь просмотры за 7 дней — тогда появится фактический multiplier.'
        };
    }

    if (actual >= video.expectedMultiplier * 0.85) {
        return {
            tone: 'green',
            label: 'Гипотеза подтверждается',
            description: 'Результат близок к ожиданию или выше. Зафиксируй угол и подумай о развитии темы.'
        };
    }

    if (isFiniteNumber(video.ctr) && video.ctr < MIN_PACKAGE_CTR) {
        return {
            tone: 'amber',
            label: 'Сигнал: проверь упаковку',
            description: `CTR ниже ${MIN_PACKAGE_CTR}%. Сначала протестируй обложку и заголовок; это не диагноз темы.`
        };
    }

    if (isFiniteNumber(video.averageViewedPercent) && video.averageViewedPercent < MIN_RETENTION) {
        return {
            tone: 'orange',
            label: 'Сигнал: проверь первые минуты',
            description: `Средний просмотр ниже ${MIN_RETENTION}%. Сравни хук, темп и обещание ролика с сильными выпусками.`
        };
    }

    return {
        tone: 'blue',
        label: 'Нужен ещё контекст',
        description: 'Результат ниже ожидания, но без явного сигнала CTR или удержания. Не делай вывод о теме по одному видео.'
    };
}

function signalClasses(tone) {
    return {
        gray: 'border-gray-700 bg-gray-800 text-gray-300',
        green: 'border-emerald-800 bg-emerald-950/40 text-emerald-200',
        amber: 'border-amber-800 bg-amber-950/40 text-amber-100',
        orange: 'border-orange-800 bg-orange-950/40 text-orange-100',
        blue: 'border-blue-800 bg-blue-950/40 text-blue-100'
    }[tone];
}

function renderSummary() {
    const reviewed = myVideos.filter(video => actualMultiplier(video) !== null);
    const met = reviewed.filter(video => actualMultiplier(video) >= video.expectedMultiplier * 0.85);
    const average = reviewed.length
        ? reviewed.reduce((sum, video) => sum + actualMultiplier(video), 0) / reviewed.length
        : null;

    $('totalVideos').textContent = myVideos.length;
    $('reviewedVideos').textContent = reviewed.length;
    $('validatedRate').textContent = reviewed.length ? `${Math.round((met.length / reviewed.length) * 100)}%` : '—';
    $('averageMultiplier').textContent = average === null ? '—' : `${formatDecimal(average)}×`;
}

function metric(label, value, suffix = '') {
    const formatted = isFiniteNumber(value) ? `${formatNumber(value)}${suffix}` : '—';
    return `<div class="rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2"><p class="text-xs text-gray-500">${label}</p><p class="mt-1 text-sm font-semibold">${formatted}</p></div>`;
}

function renderResults() {
    const container = $('resultsList');
    $('resultsCount').textContent = `${myVideos.length} ${myVideos.length === 1 ? 'видео' : 'видео'}`;

    if (!myVideos.length) {
        container.innerHTML = `
            <div class="rounded-2xl border border-dashed border-[#30363d] bg-[#161b22] px-6 py-12 text-center">
                <i class="fas fa-clipboard-check text-3xl text-gray-600"></i>
                <h3 class="mt-3 font-bold">Пока нет опубликованных видео</h3>
                <p class="mx-auto mt-2 max-w-md text-sm text-gray-500">Добавь первый ролик и его ожидание до того, как результат начнёт искажать воспоминания.</p>
            </div>`;
        return;
    }

    const ordered = [...myVideos].sort((left, right) => {
        return String(right.updatedAt).localeCompare(String(left.updatedAt));
    });

    container.innerHTML = ordered.map(video => {
        const actual = actualMultiplier(video);
        const signal = getSignal(video);
        const safeLink = isSafeUrl(video.url)
            ? `<a href="${escapeHtml(video.url)}" target="_blank" rel="noopener noreferrer" class="text-sm text-blue-400 hover:underline"><i class="fas fa-external-link-alt mr-1 text-xs"></i>Открыть на YouTube</a>`
            : '';
        const actualText = actual === null ? '—' : `${formatDecimal(actual)}×`;
        const expectationText = `${formatDecimal(video.expectedMultiplier)}×`;

        return `
            <article class="rounded-2xl border border-[#30363d] bg-[#161b22] p-5 animate-fade-in">
                <div class="flex flex-col justify-between gap-4 lg:flex-row">
                    <div class="min-w-0">
                        <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
                            <h3 class="truncate text-lg font-bold">${escapeHtml(video.title)}</h3>
                            <span class="text-xs text-gray-500">${formatDate(video.publishedAt)}</span>
                        </div>
                        <p class="mt-2 text-sm text-gray-400"><span class="text-gray-500">Гипотеза:</span> ${escapeHtml(video.topic)}</p>
                        <div class="mt-3">${safeLink}</div>
                    </div>
                    <div class="flex shrink-0 gap-2">
                        <button onclick="editVideo('${video.id}')" class="rounded-lg border border-[#30363d] bg-[#21262d] px-3 py-2 text-sm transition hover:bg-[#30363d]"><i class="fas fa-pen mr-1"></i>Изменить</button>
                        <button onclick="deleteVideo('${video.id}')" class="rounded-lg border border-red-900 bg-red-950/30 px-3 py-2 text-sm text-red-300 transition hover:bg-red-950/60" title="Удалить видео"><i class="fas fa-trash"></i></button>
                    </div>
                </div>

                <div class="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-8">
                    ${metric('Ожидание', video.expectedMultiplier, '×')}
                    ${metric('Факт за 7 дней', actual, '×')}
                    ${metric('Медиана 7 дн.', video.baselineViews)}
                    ${metric('24 часа', video.views24h)}
                    ${metric('7 дней', video.views7d)}
                    ${metric('30 дней', video.views30d)}
                    ${metric('CTR', video.ctr, '%')}
                    ${metric('Ср. просмотр', video.averageViewedPercent, '%')}
                </div>

                <div class="mt-4 rounded-xl border px-4 py-3 ${signalClasses(signal.tone)}">
                    <div class="flex flex-wrap items-baseline justify-between gap-2">
                        <p class="font-semibold"><i class="fas fa-lightbulb mr-2"></i>${signal.label}</p>
                        <p class="text-sm">Ожидание ${expectationText} · факт ${actualText}</p>
                    </div>
                    <p class="mt-1 text-sm opacity-90">${signal.description}</p>
                </div>
            </article>`;
    }).join('');
}

function render() {
    renderSummary();
    renderResults();
}

function resetForm() {
    $('videoForm').reset();
    $('editingId').value = '';
    $('publishedAt').value = new Date().toISOString().slice(0, 10);
    $('formTitle').innerHTML = '<i class="fas fa-plus-circle mr-2 text-emerald-400"></i>Добавить опубликованное видео';
    $('submitButton').innerHTML = '<i class="fas fa-save mr-2"></i>Сохранить видео';
    $('cancelEditButton').classList.add('hidden');
}

function cancelEdit() {
    resetForm();
}

function fillOptionalValue(id, value) {
    $(id).value = isFiniteNumber(value) ? value : '';
}

function editVideo(id) {
    const video = myVideos.find(item => item.id === id);
    if (!video) return;

    $('editingId').value = video.id;
    $('videoTitle').value = video.title;
    $('videoUrl').value = video.url;
    $('videoTopic').value = video.topic;
    $('publishedAt').value = video.publishedAt;
    $('expectedMultiplier').value = video.expectedMultiplier;
    $('baselineViews').value = video.baselineViews;
    fillOptionalValue('views24h', video.views24h);
    fillOptionalValue('views7d', video.views7d);
    fillOptionalValue('views30d', video.views30d);
    fillOptionalValue('impressions', video.impressions);
    fillOptionalValue('ctr', video.ctr);
    fillOptionalValue('averageViewedPercent', video.averageViewedPercent);

    $('formTitle').innerHTML = '<i class="fas fa-pen mr-2 text-emerald-400"></i>Обновить результат видео';
    $('submitButton').innerHTML = '<i class="fas fa-save mr-2"></i>Сохранить изменения';
    $('cancelEditButton').classList.remove('hidden');
    $('videoTitle').focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function deleteVideo(id) {
    const video = myVideos.find(item => item.id === id);
    if (!video || !confirm(`Удалить «${video.title}» из журнала?`)) return;
    myVideos = myVideos.filter(item => item.id !== id);
    saveVideos();
    render();
    showStatus('Видео удалено.');
    if ($('editingId').value === id) resetForm();
}

function submitVideo(event) {
    event.preventDefault();
    const title = $('videoTitle').value.trim();
    const url = $('videoUrl').value.trim();
    const topic = $('videoTopic').value.trim();
    const publishedAt = $('publishedAt').value;
    const expectedMultiplier = readOptionalNumber('expectedMultiplier');
    const baselineViews = readOptionalNumber('baselineViews');

    if (!isSafeUrl(url)) {
        showStatus('Укажи корректную ссылку на опубликованное видео.', 'error');
        return;
    }
    if (!title || !topic || !publishedAt || !isFiniteNumber(expectedMultiplier) || expectedMultiplier <= 0 || !isFiniteNumber(baselineViews) || baselineViews <= 0) {
        showStatus('Заполни название, тему, дату, ожидаемый multiplier и медиану просмотров.', 'error');
        return;
    }

    const editingId = $('editingId').value;
    const previous = myVideos.find(video => video.id === editingId);
    const record = normalizeVideo({
        id: editingId || newId().replace(/-/g, '_'),
        title,
        url,
        topic,
        publishedAt,
        expectedMultiplier,
        baselineViews,
        views24h: readOptionalNumber('views24h'),
        views7d: readOptionalNumber('views7d'),
        views30d: readOptionalNumber('views30d'),
        impressions: readOptionalNumber('impressions'),
        ctr: readOptionalNumber('ctr'),
        averageViewedPercent: readOptionalNumber('averageViewedPercent'),
        createdAt: previous?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString()
    });

    if (!record) {
        showStatus('Не удалось сохранить видео: проверь заполненные данные.', 'error');
        return;
    }

    if (previous) {
        myVideos = myVideos.map(video => video.id === record.id ? record : video);
    } else {
        myVideos.unshift(record);
    }

    saveVideos();
    render();
    resetForm();
    showStatus(previous ? 'Результат видео обновлён.' : 'Видео добавлено в журнал результатов.');
}

function exportBackup() {
    const backup = {
        version: 1,
        exportedAt: new Date().toISOString(),
        videos: myVideos
    };
    const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `buka_my_videos_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(link.href), 0);
    showStatus('Резервная копия скачана. Храни её вне браузера.');
}

function importBackup(event) {
    const [file] = event.target.files || [];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
        try {
            const parsed = JSON.parse(reader.result);
            const source = Array.isArray(parsed) ? parsed : parsed.videos;
            if (!Array.isArray(source)) throw new Error('В файле нет списка videos.');

            const imported = source.map(normalizeVideo).filter(Boolean);
            if (!imported.length && source.length) throw new Error('Не найдено корректных записей.');

            const byId = new Map(myVideos.map(video => [video.id, video]));
            imported.forEach(video => byId.set(video.id, video));
            myVideos = [...byId.values()];
            saveVideos();
            render();
            showStatus(`Импортировано записей: ${imported.length}.`);
        } catch (error) {
            showStatus(`Не удалось импортировать файл: ${error.message}`, 'error');
        } finally {
            event.target.value = '';
        }
    };
    reader.readAsText(file);
}

function init() {
    myVideos = loadVideos();
    $('videoForm').addEventListener('submit', submitVideo);
    resetForm();
    render();
}

init();
