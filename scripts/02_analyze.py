"""
АГЕНТ 2: АНАЛИТИКА + ГЕНЕРАТОР ИДЕЙ v2
VidIQ-style SEO analysis: title×3 + tags×2 + description×1
Extracts hashtags, weighted keywords, competitor tags
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "data" / "reports"
IDEAS_DIR = BASE_DIR / "data" / "reports"
IDEAS_DIR.mkdir(parents=True, exist_ok=True)

# Stop words (English + Russian)
STOP_WORDS = {
    'this', 'that', 'with', 'from', 'they', 'have', 'will', 'your', 'what', 'when', 'where',
    'which', 'their', 'them', 'than', 'then', 'more', 'some', 'time', 'very', 'just', 'like',
    'over', 'also', 'only', 'know', 'take', 'year', 'good', 'come', 'could', 'would', 'should',
    'how', 'who', 'why', 'you', 'are', 'for', 'the', 'and', 'but', 'not', 'can', 'all', 'any',
    'may', 'say', 'way', 'too', 'tell', 'much', 'about', 'after', 'back', 'other', 'many', 'now',
    'look', 'come', 'work', 'must', 'because', 'does', 'part', 'even', 'place', 'well', 'such',
    'here', 'take', 'make', 'made', 'most', 'through', 'before', 'right', 'same', 'follow',
    'around', 'want', 'show', 'every', 'form', 'great', 'think', 'say', 'help', 'turn', 'cause',
    'mean', 'move', 'live', 'play', 'went', 'light', 'kind', 'need', 'house', 'picture', 'try',
    'again', 'animal', 'point', 'mother', 'world', 'near', 'build', 'self', 'earth', 'father',
    'head', 'stand', 'page', 'country', 'found', 'answer', 'school', 'grow', 'study', 'still',
    'learn', 'plant', 'cover', 'food', 'sun', 'four', 'between', 'state', 'keep', 'eye', 'never',
    'last', 'let', 'thought', 'city', 'tree', 'cross', 'farm', 'hard', 'start', 'might', 'story',
    'saw', 'far', 'sea', 'draw', 'left', 'late', 'run', 'while', 'press', 'close', 'night', 'real',
    'life', 'few', 'north', 'open', 'seem', 'together', 'next', 'white', 'children', 'begin', 'got',
    'walk', 'example', 'ease', 'paper', 'group', 'always', 'music', 'those', 'both', 'mark', 'often',
    'letter', 'until', 'mile', 'river', 'car', 'feet', 'care', 'second', 'book', 'carry', 'took',
    'science', 'eat', 'room', 'friend', 'began', 'idea', 'fish', 'mountain', 'stop', 'once', 'base',
    'hear', 'horse', 'cut', 'sure', 'watch', 'color', 'face', 'wood', 'main', 'enough', 'plain',
    'girl', 'usual', 'young', 'ready', 'above', 'ever', 'red', 'list', 'though', 'feel', 'talk',
    'bird', 'soon', 'body', 'dog', 'family', 'direct', 'pose', 'leave', 'song', 'measure', 'door',
    'product', 'black', 'short', 'numeral', 'class', 'wind', 'question', 'happen', 'complete', 'ship',
    'area', 'half', 'rock', 'order', 'fire', 'south', 'problem', 'piece', 'told', 'knew', 'pass',
    'since', 'top', 'whole', 'king', 'space', 'heard', 'best', 'hour', 'better', 'true', 'during',
    'hundred', 'five', 'remember', 'step', 'early', 'hold', 'west', 'ground', 'interest', 'reach',
    'fast', 'verb', 'sing', 'listen', 'six', 'table', 'travel', 'less', 'morning', 'ten', 'simple',
    'several', 'vowel', 'toward', 'war', 'lay', 'against', 'pattern', 'slow', 'center', 'love',
    'person', 'money', 'serve', 'appear', 'road', 'map', 'rain', 'rule', 'govern', 'pull', 'cold',
    'notice', 'voice', 'unit', 'power', 'town', 'fine', 'certain', 'fly', 'fall', 'lead', 'cry',
    'dark', 'machine', 'note', 'wait', 'plan', 'figure', 'star', 'box', 'noun', 'field', 'rest',
    'correct', 'able', 'pound', 'done', 'beauty', 'drive', 'stood', 'contain', 'front', 'teach',
    'week', 'final', 'gave', 'green', 'oh', 'quick', 'develop', 'ocean', 'warm', 'free', 'minute',
    'strong', 'special', 'mind', 'behind', 'clear', 'tail', 'produce', 'fact', 'street', 'inch',
    'multiply', 'nothing', 'course', 'stay', 'wheel', 'full', 'force', 'blue', 'object', 'decide',
    'surface', 'deep', 'moon', 'island', 'foot', 'system', 'busy', 'test', 'record', 'boat', 'common',
    'gold', 'possible', 'plane', 'stead', 'dry', 'wonder', 'laugh', 'thousand', 'ago', 'ran', 'check',
    'game', 'shape', 'equate', 'hot', 'miss', 'brought', 'heat', 'snow', 'tire', 'bring', 'yes',
    'distant', 'fill', 'east', 'paint', 'language', 'among',
    # Russian stop words
    'это', 'как', 'что', 'так', 'вот', 'для', 'над', 'под', 'при', 'про', 'без', 'через', 'между',
    'был', 'была', 'были', 'было', 'есть', 'быть', 'может', 'можно', 'нужно', 'надо', 'очень',
    'тоже', 'даже', 'все', 'всё', 'всех', 'каждый', 'каждая', 'каждые', 'каждое', 'другой',
    'другая', 'другие', 'другое', 'такой', 'такая', 'такие', 'такое', 'который', 'которая',
    'которые', 'которое', 'свой', 'своя', 'свои', 'своё', 'наш', 'наша', 'наши', 'наше', 'ваш',
    'ваша', 'ваши', 'ваше', 'их', 'его', 'её', 'ее', 'мой', 'моя', 'мои', 'моё', 'твой', 'твоя',
    'твои', 'твоё', 'когда', 'где', 'куда', 'откуда', 'почему', 'зачем', 'какой', 'какая',
    'какие', 'какое', 'сколько', 'кто', 'чей', 'чья', 'чьи', 'чьё', 'сам', 'сама', 'сами',
    'само', 'раз', 'два', 'три', 'первый', 'второй', 'третий', 'один', 'одна', 'одни', 'одно',
    'тот', 'та', 'то', 'те', 'год', 'лет', 'день', 'дней', 'дня', 'месяц', 'месяцев', 'месяца',
    'неделя', 'недель', 'недели', 'час', 'часов', 'часа', 'минута', 'минут', 'минуты', 'секунда',
    'секунд', 'секунды', 'сегодня', 'вчера', 'завтра', 'сейчас', 'тогда', 'потом', 'после',
    'раньше', 'теперь', 'ещё', 'уже', 'только', 'лишь', 'просто', 'почти', 'около', 'более',
    'менее', 'самый', 'большой', 'маленький', 'хороший', 'плохой', 'новый', 'старый', 'другой',
    'каждый', 'любой', 'некоторый', 'такой', 'весь', 'вся', 'все', 'всё', 'много', 'мало',
    'несколько', 'пара', 'больше', 'меньше', 'лучше', 'хуже', 'более', 'менее', 'самое',
    'больше', 'меньше', 'выше', 'ниже', 'раньше', 'позже', 'чаще', 'реже', 'дальше', 'ближе'
}


def load_latest_monitor_report():
    """Find and load the most recent monitor report."""
    report_files = sorted(REPORTS_DIR.glob("monitor_report_*.json"))
    if not report_files:
        print("❌ No monitor reports found. Run Agent 1 first.")
        return None

    latest = report_files[-1]
    print(f"📂 Loading report: {latest.name}")
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_words(text):
    """Extract words from text, filtering stop words."""
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{3,}\b', text.lower())
    return [w for w in words if w not in STOP_WORDS and not w.isdigit()]


def extract_hashtags(text):
    """Extract hashtags from text."""
    if not text:
        return []
    hashtags = re.findall(r'#([a-zA-Zа-яА-ЯёЁ0-9_]+)', text.lower())
    return [h for h in hashtags if len(h) > 2]


def analyze_report(report):
    """Analyze monitor report with VidIQ-style SEO weights."""
    all_videos = []
    for channel_data in report.get('data', []):
        for video in channel_data.get('videos', []):
            video['source_channel'] = channel_data.get('channel_id', 'unknown')
            video['source_channel_title'] = channel_data.get('channel_title', 'unknown')
            video['source_subscriber_count'] = channel_data.get('subscriber_count', 0)
            all_videos.append(video)

    if not all_videos:
        print("❌ No videos to analyze")
        return None

    # Sort by metrics
    by_views = sorted(all_videos, key=lambda x: x.get('view_count', 0) or 0, reverse=True)
    by_likes = sorted(all_videos, key=lambda x: x.get('like_count', 0) or 0, reverse=True)

    # Calculate averages
    avg_views = sum(v.get('view_count', 0) or 0 for v in all_videos) / len(all_videos)
    avg_likes = sum(v.get('like_count', 0) or 0 for v in all_videos) / len(all_videos)
    avg_comments = sum(v.get('comment_count', 0) or 0 for v in all_videos) / len(all_videos)

    # ═══════════════════════════════════════════
    # WEIGHTED SEO ANALYSIS (VidIQ style)
    # ═══════════════════════════════════════════
    weighted_keywords = Counter()
    all_tags = []
    all_hashtags = []

    for v in all_videos:
        title = v.get('title', '')
        desc = v.get('description', '')
        tags = v.get('tags', [])

        # Title weight = 3
        for word in extract_words(title):
            weighted_keywords[word] += 3

        # Tags weight = 2 each
        for tag in tags:
            tag_words = extract_words(tag)
            for word in tag_words:
                weighted_keywords[word] += 2
            all_tags.append(tag.lower())

        # Description weight = 1
        for word in extract_words(desc):
            weighted_keywords[word] += 1

        # Hashtags from description
        hashtags = extract_hashtags(desc)
        all_hashtags.extend(hashtags)

    top_keywords = weighted_keywords.most_common(20)
    top_tags = Counter(all_tags).most_common(15)
    top_hashtags = Counter(all_hashtags).most_common(15)

    # Engagement rate analysis
    engagement_data = []
    for v in all_videos:
        views = v.get('view_count', 0) or 1
        likes = v.get('like_count', 0) or 0
        comments = v.get('comment_count', 0) or 0
        engagement_rate = ((likes + comments * 2) / views) * 100
        engagement_data.append({
            'title': v.get('title', '')[:60],
            'engagement_rate': round(engagement_rate, 2),
            'views': views,
            'likes': likes,
            'comments': comments,
            'video_id': v.get('video_id'),
            'channel': v.get('source_channel_title', ''),
        })

    engagement_data.sort(key=lambda x: x['engagement_rate'], reverse=True)

    return {
        'total_videos': len(all_videos),
        'avg_views': round(avg_views),
        'avg_likes': round(avg_likes),
        'avg_comments': round(avg_comments),
        'top_by_views': by_views[:5],
        'top_by_likes': by_likes[:5],
        'top_by_engagement': engagement_data[:5],
        'top_keywords': top_keywords,
        'top_tags': top_tags,
        'top_hashtags': top_hashtags,
        'all_videos': all_videos
    }


def generate_ideas(analysis):
    """Generate video ideas based on analysis."""
    ideas = []
    top_keywords = [k[0] for k in analysis.get('top_keywords', [])[:5]]
    top_hashtags = [h[0] for h in analysis.get('top_hashtags', [])[:5]]
    top_tags = [t[0] for t in analysis.get('top_tags', [])[:5]]

    # Use real data from analysis
    ideas.append({
        'id': 1,
        'category': '🔥 Тренд (высокие просмотры)',
        'idea': f'Почему видео про "{top_keywords[0] if top_keywords else "AI"}" набирают сотни тысяч просмотров — разбор от Staff-инженера',
        'format': 'Аналитика + личное мнение',
        'estimated_difficulty': 'Средняя',
        'why_works': 'Повторяет паттерн топовых видео конкурентов',
        'recommended_tags': top_tags[:5] if top_tags else [],
        'recommended_hashtags': top_hashtags[:3] if top_hashtags else []
    })

    ideas.append({
        'id': 2,
        'category': '🔥 Тренд (высокая вовлечённость)',
        'idea': 'Сколько реально зарабатывает junior-разработчик в 2026: цифры из 5 стран',
        'format': 'Инфографика + storytelling',
        'estimated_difficulty': 'Средняя',
        'why_works': 'Высокий engagement rate у "денежных" тем',
        'recommended_tags': ['salary', 'junior', 'developer', 'comparison'] + top_tags[:3] if top_tags else [],
        'recommended_hashtags': ['зарплата', 'it', 'junior'] + top_hashtags[:2] if top_hashtags else []
    })

    ideas.append({
        'id': 3,
        'category': '🎯 Пробел рынка',
        'idea': '3 ошибки в резюме, которые я вижу каждую неделю как Staff-инженер (и как их исправить)',
        'format': 'Чек-лист + примеры',
        'estimated_difficulty': 'Низкая',
        'why_works': 'Ниша "резюме" слабо покрыта конкурентами',
        'recommended_tags': ['resume', 'career', 'tips'] + top_tags[:3] if top_tags else [],
        'recommended_hashtags': ['резюме', 'карьера'] + top_hashtags[:2] if top_hashtags else []
    })

    ideas.append({
        'id': 4,
        'category': '🎯 Пробел рынка',
        'idea': 'Как я прошёл 3 собеседования в Big Tech и провалил 1 — честный разбор',
        'format': 'Storytelling + уроки',
        'estimated_difficulty': 'Низкая',
        'why_works': 'Персональные истории с провалами цепляют сильнее',
        'recommended_tags': ['interview', 'bigtech', 'experience'] + top_tags[:3] if top_tags else [],
        'recommended_hashtags': ['собеседование', 'bigtech'] + top_hashtags[:2] if top_hashtags else []
    })

    ideas.append({
        'id': 5,
        'category': '⚡ Горячая тема',
        'idea': f'AI агенты заменят программистов через 2 года? Что делать, если ты {top_keywords[0] if top_keywords else "junior"}',
        'format': 'Провокация + план действий',
        'estimated_difficulty': 'Средняя',
        'why_works': 'Тема AI в топе у всех конкурентов',
        'recommended_tags': ['ai', 'programming', 'future'] + top_tags[:3] if top_tags else [],
        'recommended_hashtags': ['ai', 'программирование'] + top_hashtags[:2] if top_hashtags else []
    })

    ideas.append({
        'id': 6,
        'category': '⚡ Горячая тема',
        'idea': 'Рынок IT 2026: кого сокращают первым и кого берут взамен',
        'format': 'Аналитика + прогноз',
        'estimated_difficulty': 'Высокая',
        'why_works': 'Страх + конкретика = высокий CTR',
        'recommended_tags': ['market', 'it', 'trends'] + top_tags[:3] if top_tags else [],
        'recommended_hashtags': ['рыноктруда', 'it'] + top_hashtags[:2] if top_hashtags else []
    })

    ideas.append({
        'id': 7,
        'category': '💡 Неожиданный угол',
        'idea': 'Почему я отказываю кандидатам с крутыми резюме — 5 реальных причин',
        'format': 'Провокация + инсайд',
        'estimated_difficulty': 'Низкая',
        'why_works': 'Реверсивный угол: не "как пройти", а "почему не берут"',
        'recommended_tags': ['hiring', 'interview', 'reverse'] + top_tags[:3] if top_tags else [],
        'recommended_hashtags': ['найм', 'собеседование'] + top_hashtags[:2] if top_hashtags else []
    })

    ideas.append({
        'id': 8,
        'category': '💡 Неожиданный угол',
        'idea': 'Сравнение: junior в России vs junior в Португалии vs junior в США — где лучше стартовать',
        'format': 'Сравнительный анализ',
        'estimated_difficulty': 'Средняя',
        'why_works': 'Твой уникальный опыт: 3 релокации + найм',
        'recommended_tags': ['relocation', 'comparison', 'junior'] + top_tags[:3] if top_tags else [],
        'recommended_hashtags': ['релокация', 'сравнение'] + top_hashtags[:2] if top_hashtags else []
    })

    ideas.append({
        'id': 9,
        'category': '📊 Формат, который цепляет',
        'idea': '10 минут правды: почему я жалею, что пошёл в IT (и 3 вещи, которые я бы сделал иначе)',
        'format': 'Short-form confession',
        'estimated_difficulty': 'Низкая',
        'why_works': 'Контринтуитивно: все хвалят IT, ты говоришь правду',
        'recommended_tags': ['confession', 'career', 'truth'] + top_tags[:3] if top_tags else [],
        'recommended_hashtags': ['it', 'карьера', 'правда'] + top_hashtags[:2] if top_hashtags else []
    })

    ideas.append({
        'id': 10,
        'category': '📊 Формат, который цепляет',
        'idea': 'Staff-инженер смотрит резюме подписчиков: разбор с комментариями',
        'format': 'Реакция + разбор',
        'estimated_difficulty': 'Низкая',
        'why_works': 'Формат "смотрю ваши X" даёт высокую вовлечённость',
        'recommended_tags': ['resume', 'review', 'reaction'] + top_tags[:3] if top_tags else [],
        'recommended_hashtags': ['резюме', 'разбор'] + top_hashtags[:2] if top_hashtags else []
    })

    return ideas


def run_analysis():
    report = load_latest_monitor_report()
    if not report:
        return

    print(f"\n{'='*60}")
    print(f"  AGENT 2: ANALYTICS + IDEA GENERATOR v2")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")

    analysis = analyze_report(report)
    if not analysis:
        return

    print("📊 СТАТИСТИКА КОНКУРЕНТОВ")
    print(f"   Всего видео проанализировано: {analysis['total_videos']}")
    print(f"   Средние просмотры: {analysis['avg_views']:,}")
    print(f"   Средние лайки: {analysis['avg_likes']:,}")
    print(f"   Средние комментарии: {analysis['avg_comments']:,}")

    print(f"\n🏆 ТОП-5 ПО ПРОСМОТРАМ:")
    for i, v in enumerate(analysis['top_by_views'][:5], 1):
        views = v.get('view_count', 0) or 0
        print(f"   {i}. {v.get('title', 'N/A')[:55]}... ({views:,} views)")

    print(f"\n💬 ТОП-5 ПО ВОВЛЕЧЁННОСТИ:")
    for i, v in enumerate(analysis['top_by_engagement'][:5], 1):
        print(f"   {i}. {v['title'][:55]}... (ER: {v['engagement_rate']}%)")

    print(f"\n🔑 ТОП КЛЮЧЕВЫХ СЛОВ (взвешенный SEO-анализ):")
    for word, score in analysis['top_keywords'][:10]:
        print(f"   • {word}: SEO-score {score}")

    if analysis['top_hashtags']:
        print(f"\n#️⃣ ТОП ХЕШТЕГОВ:")
        for tag, count in analysis['top_hashtags'][:10]:
            print(f"   • #{tag}: {count}")

    if analysis['top_tags']:
        print(f"\n🏷️ ТОП ТЕГОВ КОНКУРЕНТОВ:")
        for tag, count in analysis['top_tags'][:10]:
            print(f"   • {tag}: {count}")

    # Generate ideas
    ideas = generate_ideas(analysis)

    print(f"\n{'='*60}")
    print(f"  💡 ГЕНЕРАЦИЯ ИДЕЙ (10 идей)")
    print(f"{'='*60}\n")

    for idea in ideas:
        print(f"{idea['id']}. {idea['category']}")
        print(f"   💭 Идея: {idea['idea']}")
        print(f"   🎬 Формат: {idea['format']}")
        print(f"   📈 Почему сработает: {idea['why_works']}")
        print(f"   ⚡ Сложность: {idea['estimated_difficulty']}")
        if idea.get('recommended_tags'):
            print(f"   🏷️  Теги: {', '.join(idea['recommended_tags'][:5])}")
        if idea.get('recommended_hashtags'):
            print(f"   #️⃣  Хештеги: {' #'.join(idea['recommended_hashtags'][:3])}")
        print()

    # Save report
    today = datetime.now().strftime("%Y-%m-%d")
    report_data = {
        'date': today,
        'analysis': {
            'total_videos': analysis['total_videos'],
            'avg_views': analysis['avg_views'],
            'avg_likes': analysis['avg_likes'],
            'avg_comments': analysis['avg_comments'],
            'top_keywords': analysis['top_keywords'],
            'top_tags': analysis['top_tags'],
            'top_hashtags': analysis['top_hashtags'],
        },
        'ideas': ideas,
        'source_report': f"monitor_report_{today}.json"
    }

    report_file = IDEAS_DIR / f"ideas_report_{today}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    # Also save to dashboard data
    dash_data_dir = BASE_DIR / "dashboard" / "data"
    dash_data_dir.mkdir(parents=True, exist_ok=True)
    dash_report = dash_data_dir / f"ideas_report_{today}.json"
    with open(dash_report, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"{'='*60}")
    print(f"  ✅ ОТЧЁТ СОХРАНЁН: {report_file}")
    print(f"{'='*60}\n")

    return report_data


if __name__ == "__main__":
    run_analysis()
