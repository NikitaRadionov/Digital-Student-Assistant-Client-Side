---
name: use-case-analyst
description: >
  Use this skill whenever the user mentions Use Cases, UC, user stories, requirements, акторы, stakeholders,
  сценарии использования, функциональные требования, BPMN-to-UC mapping, или просит выявить/написать/
  проверить/улучшить Use Cases. Trigger немедленно при любых вопросах вида «какие UC нужны?»,
  «напиши Use Case для X», «проверь мой UC», «что мы упустили?», «как описать этот сценарий?».
  Скилл знает методологию Cockburn (все 13 глав), умеет вести профессиональный диалог о UC,
  выявлять UC в проекте, обнаруживать пробелы, писать fully-dressed UC и проверять по 31-тесту.
---

# Use Case Analyst Skill

Операционный скилл для профессиональной работы с Use Cases по методологии Alistair Cockburn
("Writing Effective Use Cases"). Применяется в любом контексте: выявление UC, написание,
ревизия, обнаружение пробелов, диалог о требованиях.

Перед работой:
1. Прочитай `references/use_case_methodology.md` — основной operational guide и execution methodology.
2. Используй `references/cockburn-reference.md` как canonical reference for Cockburn rules and terminology.
3. При необходимости глубокого уточнения обращайся к `source_materials/`.

---

## Knowledge Architecture

Skill uses a layered knowledge model:

- `references/use_case_methodology.md`
  Основной operational guide.
  Содержит синтез методологии Cockburn, практические правила,
  интерпретации и execution-oriented guidance.

- `references/cockburn-reference.md`
  Distilled reference layer ближе к оригинальной методологии Cockburn.
  Используется для grounding и проверки соответствия правилам.

- `source_materials/`
  Исходные главы, reminders и статьи.
  Используются для deep clarification и восстановления контекста.


## Режимы работы

### 1. ВЫЯВЛЕНИЕ — «Какие UC нужны в проекте?»

Алгоритм:
1. Попроси (или возьми из контекста): список акторов + их цели + описание системы/BPMN
2. Построй **Actor-Goal List** — таблицу «Актор → Цели (user goal level)»
3. Для каждой цели примени **Goal Level Test**:
   - ☁️ Summary: охватывает несколько сессий → оставить как Summary UC
   - 🌊 User Goal (sea-level): одна сессия, тест кофе-паузы ✓ → это основные UC
   - 🐟 Subfunction: поддерживает user goal, сложная или переиспользуется → sub UC
   - 🐚 Too Low: влить в родительский UC
4. Проверь **Silent Stakeholders** — кого не видно, но кто пострадает при сбое?
5. Выдай итоговый список с ID, именами и уровнями

### 2. НАПИСАНИЕ — «Напиши UC для X»

Алгоритм:
1. Уточни: Primary Actor, Scope, Level, контекст
2. Заполни шаблон Fully Dressed (см. `references/cockburn-reference.md` → ЧАСТЬ 2)
3. Пиши шаги строго по правилам (ЧАСТЬ 3):
   - Единственная форма: `[Актор] [активный глагол] [объект]`
   - Настоящее время, активный залог
   - Намерение, не UI-движения («Студент подаёт заявку», не «нажимает кнопку»)
   - «Validates», не «checks»
   - 3–9 шагов в Main Success Scenario
4. Brainstorm Extensions: для каждого «validates» → расширение для failure; timeout; сбой supporting actor
5. Прогони по **31-тесту** (см. `references/cockburn-reference.md` → ЧАСТЬ 8) — отметь всё, что не прошло

### 3. РЕВИЗИЯ — «Проверь мой UC»

Алгоритм:
1. Прочитай UC пользователя
2. Прогони по **31-тесту** (см. `references/cockburn-reference.md` → ЧАСТЬ 8) — выдай таблицу pass/fail с комментариями
3. Проверь **8 типичных ошибок** (см. `references/cockburn-reference.md` → ЧАСТЬ 9):
   - Нет ответа системы на действие пользователя?
   - Обезличенные шаги?
   - UI-детализация (кнопки, поля, цвета)?
   - Слишком мелкие атомарные шаги?
   - Пропущены альтернативные сценарии?
   - Нечёткие preconditions/triggers?
   - Нарушение чёрного ящика (API calls, SQL)?
   - Несколько целей в одном UC?
4. Предложи конкретные исправления с примерами

### 4. ОБНАРУЖЕНИЕ ПРОБЕЛОВ — «Что мы упустили?»

Алгоритм:
1. Возьми существующий набор UC (или Actor-Goal List)
2. Проверь по чеклисту пробелов:
   - **Silent Stakeholders** — чьи интересы не защищены? (владелец системы, аудит, регулятор)
   - **Extensions без обработки** — все «validates» имеют failure path?
   - **Supporting Actors** — есть ли UC для их сбоев?
   - **Summary покрытие** — все цели акторов попали в какой-то UC?
   - **Subfunction gaps** — какие sub UC нужны, но не выделены?
   - **Temporal gaps** — есть ли UC для отменённых/просроченных состояний?
3. Выдай список пробелов с приоритетом (критично / желательно / nice-to-have)

### 5. BPMN → UC МАППИНГ

Ключи перевода:
- Шлюзы (gateways) → Extension conditions
- MessageFlow → взаимодействие акторов в шагах
- Подпроцессы → sub use cases
- Pool/Lane границы → Scope / Primary Actor
- События (events) → Triggers / Extension *a. (любой момент)

---

## Стиль диалога

- Всегда работать на уровне **намерения**, не реализации
- Задавать уточняющие вопросы если scope/level/actor не ясны
- Ссылаться на конкретные правила Cockburn («нарушение Guideline 5», «тест кофе-паузы»)
- При написании UC — выдавать готовый текст в markdown-таблице или code block
- При ревизии — использовать таблицу pass/fail с номерами тестов

---

## Контекст проекта по умолчанию

Если пользователь упоминает «наш проект», «Digital Student Assistant», «DSA» — применять:
- **Scope:** Digital Student Assistant
- **Акторы:** Студент, Преподаватель, ЦППРП
- **Типичные цели:** Найти проект, Подать заявку, Создать проект, Рассмотреть заявку, Промодерировать проект

Детали — в `references/cockburn-reference.md` → ЧАСТЬ 13.
