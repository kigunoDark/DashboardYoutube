"""
АГЕНТ 3: СЦЕНАРИСТ
Генерирует сценарии для YouTube-видео на основе идей из Агента 2.
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "data" / "reports"
SCRIPTS_DIR = BASE_DIR / "data" / "reports"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


def load_latest_ideas_report():
    """Find and load the most recent ideas report."""
    report_files = sorted(REPORTS_DIR.glob("ideas_report_*.json"))
    if not report_files:
        print("❌ No ideas reports found. Run Agent 2 first.")
        return None
    
    latest = report_files[-1]
    print(f"📂 Loading ideas report: {latest.name}")
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_script_prompt(idea):
    """Generate a detailed LLM prompt for a YouTube script."""
    return f"""Ты — опытный сценарист YouTube-канала BUKA. Канал ведёт Влад — Staff-инженер с 10-летним опытом, трижды переезжавший.

Напиши сценарий для видео на тему: "{idea['idea']}"

Формат канала:
- Честный разговор без корпоративных сказок
- Разговорный стиль, как с другом за пивом
- Короткие предложения, конкретика, цифры
- Персональные истории из опыта

СТРУКТУРА СЦЕНАРИЯ (10-12 минут):

## [ХУК] 0:00-0:30 (первые 30 секунд — решают всё)
- Начни НЕ с приветствия
- Начни с провокации, цифры или личной истории
- Обещи конкретный результат: "После этого видео ты исправишь резюме и тебя заметят"

## [ОСНОВНАЯ ЧАСТЬ] 0:30-9:00
- 3 ошибки с примерами
- Для каждой ошибки: что не так → почему это важно → как исправить
- Добавь личные истории ("Я помню, как отклонил кандидата с Google в резюме, потому что...")

## [ЗАКЛЮЧЕНИЕ] 9:00-10:00
- Краткий пересказ 3 ошибок
- Призыв к действию: подписка, комментарий, лайк
- Тизер следующего видео

ТРЕБОВАНИЯ:
- Разбей на таймкоды
- Укажи, что показывать на экране (скриншоты, графика)
- Используй жирный шрифт для акцентов
- Длина: 1500-2000 слов
"""


def generate_script_template(idea):
    """Generate a script template that can be filled in manually or by LLM."""
    
    template = f"""# СЦЕНАРИЙ: {idea['idea']}

**Длительность:** 10-12 минут  
**Формат:** {idea['format']}  
**Дата создания:** {datetime.now().strftime('%Y-%m-%d')}  

---

## [ХУК] 0:00 — 0:30

**[ВЛАД смотрит прямо в камеру, серьёзный тон]**

> "Я отклонил 47 кандидатов за последние 3 месяца. Не потому что они плохие специалисты. А потому что их резюме говорит одно: 'я не умею продавать себя'. И сегодня я покажу 3 ошибки, которые я вижу каждую неделю. Исправь их — и тебя заметят."

**[На экране: миниатюры резюме с зачёркнутыми элементами]**

---

## [ОШИБКА 1] 0:30 — 3:30

### Название ошибки: [ВСТАВИТЬ]

**[ВЛАД]**
> "Первая ошибка — ..."

**Пример:**
- [Конкретный пример из практики]

**Почему это проблема:**
- [Объяснение]

**Как исправить:**
1. [Шаг 1]
2. [Шаг 2]
3. [Шаг 3]

**[На экране: before/after резюме]**

---

## [ОШИБКА 2] 3:30 — 6:30

### Название ошибки: [ВСТАВИТЬ]

**[ВЛАД]**
> "Вторая ошибка хуже. ..."

**Пример:**
- [Конкретный пример]

**Почему это проблема:**
- [Объяснение]

**Как исправить:**
1. [Шаг 1]
2. [Шаг 2]

**[На экране: скриншот реального резюме с комментариями]**

---

## [ОШИБКА 3] 6:30 — 9:00

### Название ошибки: [ВСТАВИТЬ]

**[ВЛАД]**
> "И третья ошибка — та, из-за которой я отклонил кандидата с Amazon вчера. ..."

**Пример:**
- [Личная история]

**Почему это проблема:**
- [Объяснение]

**Как исправить:**
1. [Шаг 1]
2. [Шаг 2]
3. [Шаг 3]

---

## [ЗАКЛЮЧЕНИЕ] 9:00 — 10:00

**[ВЛАД]**
> "Итак, три ошибки: [краткий пересказ]. Исправь их — и количество откликов вырастет минимум в 2 раза. Гарантирую."

> "Если это видео было полезным — поставь лайк и напиши в комментариях, какая ошибка была у тебя. Читаю всё. А в следующем видео разберу 5 вопросов, которые задают на собеседованиях в Big Tech. Подпишись, чтобы не пропустить."

**[На экране: стрелка на кнопку подписки]**

---

## ЧЕК-ЛИСТ ДО СЪЁМКИ

- [ ] Подготовить примеры резюме (before/after)
- [ ] Найти скриншоты реальных резюме (без личных данных)
- [ ] Подготовить графику: 3 ошибки в виде списка
- [ ] Проверить освещение и звук
- [ ] Зарядить камеру

---

*Сгенерировано Агентом 3 (Сценарист) — YouTube System BUKA*
"""
    return template


def run_scriptwriter():
    report = load_latest_ideas_report()
    if not report:
        return
    
    print(f"\n{'='*60}")
    print(f"  AGENT 3: SCRIPTWRITER")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")
    
    ideas = report.get('ideas', [])
    if not ideas:
        print("❌ No ideas found in report")
        return
    
    # Generate scripts for top 3 ideas (low difficulty first)
    low_difficulty = [i for i in ideas if i.get('estimated_difficulty') == 'Низкая']
    target_ideas = low_difficulty[:3] if low_difficulty else ideas[:3]
    
    print(f"Generating scripts for {len(target_ideas)} ideas...\n")
    
    generated_scripts = []
    
    for idx, idea in enumerate(target_ideas, 1):
        print(f"[{idx}/{len(target_ideas)}] Processing: {idea['idea'][:50]}...")
        
        # Generate LLM prompt
        llm_prompt = generate_script_prompt(idea)
        
        # Generate template
        template = generate_script_template(idea)
        
        # Save individual files
        safe_name = idea['idea'][:30].replace(' ', '_').replace('?', '').replace(':', '')
        
        # Save LLM prompt
        prompt_file = SCRIPTS_DIR / f"script_prompt_{safe_name}.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(llm_prompt)
        
        # Save template
        template_file = SCRIPTS_DIR / f"script_template_{safe_name}.md"
        with open(template_file, "w", encoding="utf-8") as f:
            f.write(template)
        
        generated_scripts.append({
            'idea_id': idea['id'],
            'idea': idea['idea'],
            'prompt_file': str(prompt_file),
            'template_file': str(template_file),
        })
        
        print(f"  ✅ Prompt saved: {prompt_file.name}")
        print(f"  ✅ Template saved: {template_file.name}\n")
    
    # Save index
    today = datetime.now().strftime('%Y-%m-%d')
    index = {
        'date': today,
        'generated_scripts': generated_scripts,
        'instructions': {
            'step_1': 'Open the prompt file and copy the text',
            'step_2': 'Paste into Kimi / ChatGPT / Claude',
            'step_3': 'Get full script and fill the template',
            'step_4': 'Use the template for filming guidance',
        }
    }
    
    index_file = SCRIPTS_DIR / f"scripts_index_{today}.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # Also save to dashboard data (dated + "latest" alias for the dashboard)
    dash_data_dir = BASE_DIR / "dashboard" / "data"
    dash_data_dir.mkdir(parents=True, exist_ok=True)
    for name in (f"scripts_index_{today}.json", "scripts_index_latest.json"):
        with open(dash_data_dir / name, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"{'='*60}")
    print(f"  ✅ ALL SCRIPTS GENERATED")
    print(f"  Index: {index_file}")
    print(f"{'='*60}\n")
    
    return index


if __name__ == "__main__":
    run_scriptwriter()
