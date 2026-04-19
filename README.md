# Digital-Student-Assistant

**Цифровой Ассистент Студента** — рекомендательная система студенческих проектов.

![CI](https://github.com/krevetka-is-afk/Digital-Student-Assistant/actions/workflows/ci.yml/badge.svg)

---

## Моя часть проекта — SSR Frontend

Ниже представлены файлы и директории, реализованные в рамках данной курсовой работы.
Всё остальное (DRF API, ML-сервис, модели предметной области, инфраструктура) — бэкенд, написанный отдельно.

```
src/web/
│
├── apps/
│   │
│   ├── frontend/                        ← Django-приложение SSR frontend
│   │   ├── views/
│   │   │   ├── auth.py                  Вход и регистрация
│   │   │   ├── projects.py              Каталог, детали, создание/редактирование,
│   │   │   │                            рекомендации, закладки, инициативные проекты
│   │   │   ├── applications.py          Подача заявки, список заявок студента
│   │   │   ├── moderation.py            Очередь модерации, решение по проекту
│   │   │   └── profile.py              Личный кабинет
│   │   ├── templatetags/
│   │   │   └── frontend_extras.py       Кастомные теги: get_item, role_label
│   │   ├── tests/
│   │   │   ├── conftest.py              Django setup для pytest
│   │   │   └── test_frontend_views.py   19 тестов frontend-views
│   │   └── urls.py                      Все URL-маршруты frontend
│   │
│   └── projects/
│       └── migrations/
│           ├── 0007_bookmark.py         Новая модель Bookmark (user × project)
│           └── 0008_add_supervisor_name.py  Поле supervisor_name у Project
│
└── templates/
    └── frontend/
        ├── auth.html                    Страница входа / регистрации
        ├── project_list.html            Каталог с вкладками (рек., закладки, заявки)
        ├── project_detail.html          Страница проекта
        ├── project_form.html            Форма создания / редактирования проекта
        ├── initiative_form.html         Форма инициативного проекта (студент)
        ├── moderation_list.html         Очередь модерации
        ├── project_applications.html    Заявки на проект (для заказчика)
        ├── profile.html                 Личный кабинет
        └── partials/
            ├── apply_button.html        Кнопка «Откликнуться» (HTMX swap)
            ├── apply_action_detail.html Блок отклика на странице проекта
            ├── bookmark_button.html     Кнопка закладки (outline / filled)
            └── projects_grid.html       Сетка карточек (HTMX partial)
```

### Что реализовано

**Экраны (все роли):**

| Экран | URL | Роль |
|-------|-----|------|
| Вход / регистрация | `/auth/` | Все |
| Каталог проектов | `/projects/` | Все |
| Страница проекта | `/projects/<id>/` | Все |
| Личный кабинет | `/profile/` | Все |
| Форма проекта | `/projects/create/`, `/projects/<id>/edit/` | Заказчик |
| Инициативный проект | `/projects/initiative/` | Студент |
| Заявки на проект | `/projects/<id>/applications/` | Заказчик |
| Очередь модерации | `/moderation/` | Модератор |

**Ключевые UX-решения:**
- Каталог `/projects/` — четыре вкладки без перезагрузки (JS show/hide): «Все проекты», «Рекомендации», «Закладки», «Мои заявки»; переключение по `?tab=` URL-параметру — работают прямые ссылки из профиля
- Поиск и фильтры через HTMX с debounce 350 мс — обновляется только сетка, URL меняется без перезагрузки (`hx-push-url`)
- Закладки — оптимистичное обновление UI (иконка меняется сразу, откат при ошибке сервера)
- Shared apply modal — одно модальное окно на всю страницу, корректно закрывается и обновляет только нужную карточку
- Интересы студента становятся кликабельными фильтрами в каталоге
- Все защищённые страницы требуют авторизации (`@login_required`)

---

## Возможности платформы

### Для студентов
- **Каталог проектов** — поиск по названию, фильтрация по технологиям и размеру команды
- **Рекомендации** — ML-подбор проектов на основе интересов из профиля
- **Закладки** — сохранение понравившихся проектов
- **Заявки** — подача с мотивационным письмом, отслеживание статуса
- **Инициативные проекты** — студент предлагает собственный проект → уходит на проверку модератору
- **Профиль** — редактирование имени, «О себе», интересов

### Для заказчиков
- Создание и редактирование проектов
- Отправка проектов на модерацию
- Просмотр и рецензирование заявок (принять / отклонить)

### Для модераторов (ЦППРП)
- Очередь проектов: одобрить или отклонить с обязательным комментарием

---

## Архитектура

| Компонент | Стек |
|-----------|------|
| Web-сервис | Django 6.0, DRF, HTMX 1.9, Tailwind CSS v2 |
| ML-сервис | FastAPI, keyword-heuristic (готов к подключению sentence-transformers) |
| БД | PostgreSQL 16 |
| Инфраструктура | Docker Compose |

ML-сервис подключается опционально — при недоступности Django автоматически переключается на keyword-fallback.

---

## Запуск

### Django (локально)

```bash
cd src/web/
cp .env.example .env
uv sync --group dev
uv run python manage.py migrate
uv run python manage.py runserver --settings=config.settings.dev
```

- Главная: `http://127.0.0.1:8000/`
- Проекты: `http://127.0.0.1:8000/projects/`

### ML-сервис (опционально)

```bash
cd src/ml/
uv sync
uv run uvicorn app.main:app --port 8001 --reload
```

### Docker (всё сразу)

```bash
docker compose -f infra/docker-compose.yml --profile dev up --build
```

---

## Тесты

```bash
cd src/web
uv run pytest                          # все тесты
uv run pytest apps/frontend/tests/    # frontend-views (19 тестов)
uv run pytest apps/recs/tests/        # ML-gateway (8 тестов)
```

Покрытие frontend-тестов: каталог, закладки, инициативные проекты, профиль, редиректы, права доступа, защита от анонимного доступа.

---

## Документация проекта

| Файл | Назначение |
|------|-----------|
| `DEVLOG.md` | Журнал разработки — что и когда было сделано, ссылки на файлы |
| `BUGLOG.md` | Журнал проблем — что случилось, почему, как исправлено |
| `Список экранов.md` | Спецификация всех экранов и бизнес-логики |
| `BPMN diagram.bpmn` | BPMN-диаграмма бизнес-процессов |

---

## Issues

1. [Bug report](.github/ISSUE_TEMPLATE/bug_report.yml)
2. [Feature request](.github/ISSUE_TEMPLATE/feature.yml)
