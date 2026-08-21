# Один YouTube-канал: автоматический Feedback

Этот вариант не использует Supabase, Vercel API или отдельный личный кабинет. GitHub Actions получает метрики одного вашего канала и сохраняет обычный JSON, который читает сайт.

## Что нужно сделать один раз

1. В Google Cloud создай OAuth Client типа **Web application**, добавь Authorized redirect URI `https://developers.google.com/oauthplayground` и включи **YouTube Data API v3** и **YouTube Analytics API**.
2. В OAuth consent screen добавь свой Google-аккаунт в Test users.
3. Открой [OAuth 2.0 Playground](https://developers.google.com/oauthplayground), нажми шестерёнку, включи **Use your own OAuth credentials** и укажи Client ID / Client Secret.
4. Выбери и авторизуй scopes:
   - `https://www.googleapis.com/auth/youtube.readonly`
   - `https://www.googleapis.com/auth/yt-analytics.readonly`
   - `https://www.googleapis.com/auth/yt-analytics-monetary.readonly`
5. Нажми **Exchange authorization code for tokens** и скопируй `refresh_token`.
6. В GitHub → **Settings → Secrets and variables → Actions** добавь три repository secrets:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `YOUTUBE_REFRESH_TOKEN`
7. Запусти Actions → **collect** → **Run workflow**. После успешного запуска появится `dashboard/data/my_videos_latest.json`, а сайт начнёт показывать данные в «Мои результаты».

Секреты не добавляй в файлы и не присылай в чат. Refresh token позволяет обновлять метрики без повторного входа.

## Что будет обновляться

Просмотры за 24 часа, 7 и 30 дней; показы; CTR; средний процент просмотра; лайки; комментарии; подписки от ролика и оценочный доход за 30 дней. Доход может отсутствовать, если YouTube не выдаёт его вашему каналу — это не ошибка.
