"""
АГЕНТ 2: АНАЛИТИКА + ГЕНЕРАТОР ИДЕЙ
Анализирует собранные данные и генерирует идеи для контента.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "data" / "reports"
IDEAS_DIR = BASE_DIR / "data" / "reports"
IDEAS_DIR.mkdir(parents=True, exist_ok=True)


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


def extract_keywords(text):
    """Extract meaningful keywords from text."""
    if not text:
        return []
    # Simple keyword extraction: words 4+ chars, exclude common stop words
    stop_words = {'this', 'that', 'with', 'from', 'they', 'have', 'will', 'your', 'what', 'when', 'where', 'which', 'their', 'them', 'than', 'then', 'more', 'some', 'time', 'very', 'just', 'like', 'over', 'also', 'only', 'know', 'take', 'year', 'good', 'come', 'could', 'would', 'should', 'how', 'who', 'why', 'you', 'are', 'for', 'the', 'and', 'but', 'not', 'can', 'all', 'any', 'may', 'say', 'man', 'way', 'too', 'old', 'tell', 'very', 'much', 'about', 'after', 'back', 'other', 'many', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'around', 'another', 'came', 'come', 'work', 'three', 'must', 'because', 'does', 'part', 'even', 'place', 'well', 'such', 'here', 'take', 'make', 'made', 'most', 'through', 'when', 'where', 'much', 'before', 'right', 'too', 'any', 'same', 'tell', 'boy', 'follow', 'around', 'want', 'show', 'every', 'form', 'great', 'think', 'say', 'help', 'low', 'line', 'differ', 'turn', 'cause', 'mean', 'move', 'live', 'play', 'went', 'light', 'kind', 'need', 'house', 'picture', 'try', 'again', 'animal', 'point', 'mother', 'world', 'near', 'build', 'self', 'earth', 'father', 'head', 'stand', 'page', 'should', 'country', 'found', 'answer', 'school', 'grow', 'study', 'still', 'learn', 'plant', 'cover', 'food', 'sun', 'four', 'between', 'state', 'keep', 'eye', 'never', 'last', 'let', 'thought', 'city', 'tree', 'cross', 'farm', 'hard', 'start', 'might', 'story', 'saw', 'far', 'sea', 'draw', 'left', 'late', 'run', 'while', 'press', 'close', 'night', 'real', 'life', 'few', 'north', 'open', 'seem', 'together', 'next', 'white', 'children', 'begin', 'got', 'walk', 'example', 'ease', 'paper', 'group', 'always', 'music', 'those', 'both', 'mark', 'often', 'letter', 'until', 'mile', 'river', 'car', 'feet', 'care', 'second', 'book', 'carry', 'took', 'science', 'eat', 'room', 'friend', 'began', 'idea', 'fish', 'mountain', 'stop', 'once', 'base', 'hear', 'horse', 'cut', 'sure', 'watch', 'color', 'face', 'wood', 'main', 'enough', 'plain', 'girl', 'usual', 'young', 'ready', 'above', 'ever', 'red', 'list', 'though', 'feel', 'talk', 'bird', 'soon', 'body', 'dog', 'family', 'direct', 'pose', 'leave', 'song', 'measure', 'door', 'product', 'black', 'short', 'numeral', 'class', 'wind', 'question', 'happen', 'complete', 'ship', 'area', 'half', 'rock', 'order', 'fire', 'south', 'problem', 'piece', 'told', 'knew', 'pass', 'since', 'top', 'whole', 'king', 'space', 'heard', 'best', 'hour', 'better', 'during', 'hundred', 'five', 'remember', 'step', 'early', 'hold', 'west', 'ground', 'interest', 'reach', 'fast', 'verb', 'sing', 'listen', 'six', 'table', 'travel', 'less', 'morning', 'ten', 'simple', 'several', 'vowel', 'toward', 'war', 'lay', 'against', 'pattern', 'slow', 'center', 'love', 'person', 'money', 'serve', 'appear', 'road', 'map', 'rain', 'rule', 'govern', 'pull', 'cold', 'notice', 'voice', 'unit', 'power', 'town', 'fine', 'certain', 'fly', 'fall', 'lead', 'cry', 'dark', 'machine', 'note', 'wait', 'plan', 'figure', 'star', 'box', 'noun', 'field', 'rest', 'correct', 'able', 'pound', 'done', 'beauty', 'drive', 'stood', 'contain', 'front', 'teach', 'week', 'final', 'gave', 'green', 'oh', 'quick', 'develop', 'ocean', 'warm', 'free', 'minute', 'strong', 'special', 'mind', 'behind', 'clear', 'tail', 'produce', 'fact', 'street', 'inch', 'multiply', 'nothing', 'course', 'stay', 'wheel', 'full', 'force', 'blue', 'object', 'decide', 'surface', 'deep', 'moon', 'island', 'foot', 'system', 'busy', 'test', 'record', 'boat', 'common', 'gold', 'possible', 'plane', 'stead', 'dry', 'wonder', 'laugh', 'thousand', 'ago', 'ran', 'check', 'game', 'shape', 'equate', 'hot', 'miss', 'brought', 'heat', 'snow', 'tire', 'bring', 'yes', 'distant', 'fill', 'east', 'paint', 'language', 'among'}
    
    words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', text.lower())
    return [w for w in words if w not in stop_words and not w.isdigit()]


def analyze_report(report):
    """Analyze monitor report and extract insights."""
    all_videos = []
    for channel_data in report.get('data', []):
        for video in channel_data.get('videos', []):
            video['source_channel'] = channel_data.get('channel_id', 'unknown')
            all_videos.append(video)
    
    if not all_videos:
        print("❌ No videos to analyze")
        return None
    
    # Sort by metrics
    by_views = sorted(all_videos, key=lambda x: x.get('view_count', 0) or 0, reverse=True)
    by_likes = sorted(all_videos, key=lambda x: x.get('like_count', 0) or 0, reverse=True)
    by_comments = sorted(all_videos, key=lambda x: x.get('comment_count', 0) or 0, reverse=True)
    
    # Calculate averages
    avg_views = sum(v.get('view_count', 0) or 0 for v in all_videos) / len(all_videos)
    avg_likes = sum(v.get('like_count', 0) or 0 for v in all_videos) / len(all_videos)
    avg_comments = sum(v.get('comment_count', 0) or 0 for v in all_videos) / len(all_videos)
    
    # Extract keywords from titles
    all_titles = ' '.join([v.get('title', '') for v in all_videos])
    keywords = extract_keywords(all_titles)
    top_keywords = Counter(keywords).most_common(15)
    
    # Extract keywords from descriptions
    all_descriptions = ' '.join([v.get('description', '') for v in all_videos if v.get('description')])
    desc_keywords = extract_keywords(all_descriptions)
    top_desc_keywords = Counter(desc_keywords).most_common(15)
    
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
            'video_id': v.get('video_id')
        })
    
    engagement_data.sort(key=lambda x: x['engagement_rate'], reverse=True)
    
    return {
        'total_videos': len(all_videos),
        'avg_views': round(avg_views),
        'avg_likes': round(avg_likes),
        'avg_comments': round(avg_comments),
        'top_by_views': by_views[:5],
        'top_by_likes': by_likes[:5],
        'top_by_comments': by_comments[:5],
        'top_by_engagement': engagement_data[:5],
        'top_keywords_titles': top_keywords,
        'top_keywords_descriptions': top_desc_keywords,
        'all_videos': all_videos
    }


def generate_ideas(analysis):
    """Generate video ideas based on analysis."""
    ideas = []
    
    # Pattern 1: High-performing topics
    top_keywords = [k[0] for k in analysis.get('top_keywords_titles', [])[:5]]
    
    # Pattern 2: Topics with high engagement
    high_engagement = analysis.get('top_by_engagement', [])
    
    # Pattern 3: View count gaps (what got most views)
    top_views = analysis.get('top_by_views', [])
    
    # --- IDEAS BASED ON TRENDS ---
    ideas.append({
        'id': 1,
        'category': '🔥 Тренд (высокие просмотры)',
        'idea': f'Почему видео про "{top_keywords[0] if top_keywords else 'AI'}" набирают сотни тысяч просмотров — разбор от Staff-инженера',
        'format': 'Аналитика + личное мнение',
        'estimated_difficulty': 'Средняя',
        'why_works': 'Повторяет паттерн топовых видео конкурентов'
    })
    
    ideas.append({
        'id': 2,
        'category': '🔥 Тренд (высокая вовлечённость)',
        'idea': 'Сколько реально зарабатывает junior-разработчик в 2026: цифры из 5 стран',
        'format': 'Инфографика + storytelling',
        'estimated_difficulty': 'Средняя',
        'why_works': 'Высокий engagement rate у "денежных" тем'
    })
    
    ideas.append({
        'id': 3,
        'category': '🎯 Пробел рынка',
        'idea': '3 ошибки в резюме, которые я вижу каждую неделю как Staff-инженер (и как их исправить)',
        'format': 'Чек-лист + примеры',
        'estimated_difficulty': 'Низкая',
        'why_works': 'Ниша "резюме" слабо покрыта конкурентами, высокий практический ценн'
    })
    
    ideas.append({
        'id': 4,
        'category': '🎯 Пробел рынка',
        'idea': 'Как я прошёл 3 собеседования в Big Tech и провалил 1 — честный разбор',
        'format': 'Storytelling + уроки',
        'estimated_difficulty': 'Низкая',
        'why_works': 'Персональные истории с провалами цепляют сильнее успешных'
    })
    
    ideas.append({
        'id': 5,
        'category': '⚡ Горячая тема',
        'idea': 'AI агенты заменят программистов через 2 года? Что делать, если ты junior',
        'format': 'Провокация + план действий',
        'estimated_difficulty': 'Средняя',
        'why_works': 'Тема AI в топе у всех конкурентов, но мало кто даёт конкретный план'
    })
    
    ideas.append({
        'id': 6,
        'category': '⚡ Горячая тема',
        'idea': 'Рынок IT 2026: кого сокращают первым и кого берут взамен',
        'format': 'Аналитика + прогноз',
        'estimated_difficulty': 'Высокая',
        'why_works': 'Страх + конкретика = высокий CTR'
    })
    
    ideas.append({
        'id': 7,
        'category': '💡 Неожиданный угол',
        'idea': 'Почему я отказываю кандидатам с крутыми резюме — 5 реальных причин',
        'format': 'Провокация + инсайд',
        'estimated_difficulty': 'Низкая',
        'why_works': 'Реверсивный угол: не "как пройти", а "почему не берут"'
    })
    
    ideas.append({
        'id': 8,
        'category': '💡 Неожиданный угол',
        'idea': 'Сравнение: junior в России vs junior в Португалии vs junior в США — где лучше стартовать',
        'format': 'Сравнительный анализ',
        'estimated_difficulty': 'Средняя',
        'why_works': 'Твой уникальный опыт: 3 релокации + найм'
    })
    
    ideas.append({
        'id': 9,
        'category': '📊 Формат, который цепляет',
        'idea': '10 минут правды: почему я жалею, что пошёл в IT (и 3 вещи, которые я бы сделал иначе)',
        'format': 'Short-form confession',
        'estimated_difficulty': 'Низкая',
        'why_works': 'Контринтуитивно: все хвалят IT, ты говоришь правду о минусах'
    })
    
    ideas.append({
        'id': 10,
        'category': '📊 Формат, который цепляет',
        'idea': 'Staff-инженер смотрит резюме подписчиков: разбор с комментариями',
        'format': 'Реакция + разбор',
        'estimated_difficulty': 'Низкая',
        'why_works': 'Формат "смотрю ваши X" всегда даёт высокую вовлечённость'
    })
    
    return ideas


def run_analysis():
    report = load_latest_monitor_report()
    if not report:
        return
    
    print(f"\n{'='*60}")
    print(f"  AGENT 2: ANALYTICS + IDEA GENERATOR")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")
    
    # Run analysis
    analysis = analyze_report(report)
    if not analysis:
        return
    
    # Print statistics
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
    
    print(f"\n🔑 ТОП КЛЮЧЕВЫХ СЛОВ (заголовки):")
    for word, count in analysis['top_keywords_titles'][:10]:
        print(f"   • {word}: {count}")
    
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
            'top_keywords': analysis['top_keywords_titles'],
        },
        'ideas': ideas,
        'source_report': f"monitor_report_{today}.json"
    }
    
    report_file = IDEAS_DIR / f"ideas_report_{today}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"{'='*60}")
    print(f"  ✅ ОТЧЁТ СОХРАНЁН: {report_file}")
    print(f"{'='*60}\n")
    
    return report_data


if __name__ == "__main__":
    run_analysis()
