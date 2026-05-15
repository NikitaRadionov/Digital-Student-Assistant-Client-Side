# Business Rules

> **System:** Цифровой Студенческий Ассистент  
> **Scope:** Application-level business rules, extracted from models, transitions, views  
> **Sources:** `apps/applications/models.py`, `apps/projects/models.py`, `apps/*/transitions.py`, `apps/frontend/views/`  

---

## Заявки (Applications)

| ID        | Правило                                                                                                     | Источник в коде                                               |
| --------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| BR-APP-01 | Одна заявка на пару `(project_id, applicant_id)` — UniqueConstraint на уровне БД                            | `Application.Meta.constraints`                                |
| BR-APP-02 | Проект принимает заявки только при: `status == PUBLISHED` **AND** `accepted_participants_count < team_size` | `views/applications.py: _project_accepts_applications()`      |
| BR-APP-03 | Право подачи заявки — только роль `STUDENT` (`is_staff = False`)                                            | `views/applications.py: apply_to_project, submit_application` |
| BR-APP-04 | Мотивационный текст при первичной подаче необязателен                                                       | `views/applications.py: submit_application`                   |
| BR-APP-05 | При редактировании существующей заявки мотивация должна быть не короче 30 символов                          | `views/applications.py: edit_application`                     |
| BR-APP-06 | Рецензировать заявку вправе только владелец проекта (роль `CUSTOMER`) или `is_staff`                        | `transitions/applications.py: _can_review_application()`      |
| BR-APP-07 | Отклонение заявки требует комментария длиной не менее 50 символов                                           | `transitions/applications.py: review_application`             |
| BR-APP-08 | Отозвать можно только заявку со статусом `SUBMITTED`; заявка физически удаляется из БД                      | `views/applications.py: withdraw_application`                 |
| BR-APP-09 | Редактировать можно только заявку со статусом `SUBMITTED`                                                   | `views/applications.py: edit_application`                     |

---

## Проекты (Projects)

| ID | Правило | Источник в коде |
|---|---|---|
| BR-PRJ-01 | Создавать проекты-черновики вправе только роль `CUSTOMER` | `views/projects.py: @customer_required` |
| BR-PRJ-02 | Инициативный проект создаёт только роль `STUDENT`; `source_type = INITIATIVE` | `views/projects.py: @student_required, initiative_project_create` |
| BR-PRJ-03 | Инициативный проект создаётся сразу в статусе `ON_MODERATION` (без стадии DRAFT) | `views/projects.py: initiative_project_create` |
| BR-PRJ-04 | Проект-черновик (supervisor) создаётся в статусе `DRAFT`; требует отдельного шага отправки на модерацию | `views/projects.py: project_create` |
| BR-PRJ-05 | Отправить на модерацию можно только из статусов: `DRAFT`, `REVISION_REQUESTED`, `SUPERVISOR_REVIEW` | `transitions/projects.py: submit_project_for_moderation` |
| BR-PRJ-06 | Редактирование проекта заблокировано при статусах: `PUBLISHED`, `STAFFED`, `ARCHIVED` | `views/projects.py: _LOCKED_STATUSES` |
| BR-PRJ-07 | Удалить проект можно только при статусах: `DRAFT`, `REJECTED` | `views/projects.py: _DELETABLE_STATUSES` |
| BR-PRJ-08 | `team_size` для проектов преподавателя: 1–100; для инициативных — 1–10 | `InitiativeProjectForm.team_size: max_value=10` |
| BR-PRJ-09 | Описание проекта необязательно для преподавателя; обязательно для инициативного проекта | `ProjectFrontendForm` vs `InitiativeProjectForm` |

---

## Модерация проектов

| ID | Правило | Источник в коде |
|---|---|---|
| BR-MOD-01 | Модерировать проекты вправе только роль `CPPRP` или `is_staff` | `transitions/projects.py: _is_cpprp_or_staff()` |
| BR-MOD-02 | На модерацию принимаются только проекты со статусом `ON_MODERATION` | `transitions/projects.py: moderate_project` |
| BR-MOD-03 | Отклонение на модерации требует комментария длиной не менее 100 символов | `transitions/projects.py: moderate_project` |
| BR-MOD-04 | При отклонении supervisor-проекта — статус становится `REJECTED` (терминальный) | `transitions/projects.py: moderate_project` |
| BR-MOD-05 | При отклонении initiative-проекта — статус становится `REVISION_REQUESTED` (проект можно доработать и переотправить) | `transitions/projects.py: moderate_project` |
| BR-MOD-06 | При одобрении — статус становится `PUBLISHED` для любого `source_type` | `transitions/projects.py: moderate_project` |

---

## Укомплектованность проекта (Staffing)

| ID | Правило | Источник в коде |
|---|---|---|
| BR-STA-01 | После каждого решения по заявке система автоматически пересчитывает `accepted_participants_count` | `transitions/projects.py: recalculate_project_staffing` |
| BR-STA-02 | Если `accepted_participants_count ≥ team_size` — статус автоматически меняется с `PUBLISHED` на `STAFFED` | `transitions/projects.py: recalculate_project_staffing` |
| BR-STA-03 | Если `accepted_participants_count < team_size` — статус автоматически возвращается с `STAFFED` на `PUBLISHED` | `transitions/projects.py: recalculate_project_staffing` |
| BR-STA-04 | Укомплектованность пересчитывается только при статусах `PUBLISHED` и `STAFFED` | `transitions/projects.py: recalculate_project_staffing` |

---

## Профиль и авторизация

| ID | Правило | Источник в коде |
|---|---|---|
| BR-USR-01 | Доступ к платформе требует авторизации; неавторизованные пользователи перенаправляются на `/auth/` | `@login_required(login_url="/auth/")` |
| BR-USR-02 | Поле `interests` профиля студента: максимум 20 тегов, каждый 2–50 символов | `views/profile.py: _INTERESTS_MAX, _INTEREST_ITEM_MIN/MAX` |
| BR-USR-03 | `bio` профиля: если указан — не менее 10 и не более 500 символов | `views/profile.py: _BIO_MIN, _BIO_MAX` |

---

## Жизненный цикл статусов (справочно)

### Application.status

```
SUBMITTED → ACCEPTED  (review_application, decision="accept")
SUBMITTED → REJECTED  (review_application, decision="reject", comment ≥ 50 chars)
SUBMITTED → [deleted] (withdraw_application, студент)
```

### Project.status — Supervisor-проект (source_type = SUPERVISOR)

```
DRAFT
  → ON_MODERATION      (submit_project_for_moderation)
    → PUBLISHED        (moderate_project, decision="approve")
    → REJECTED         (moderate_project, decision="reject") [terminal]
  → REVISION_REQUESTED [только из DRAFT, если был ещё один цикл]
  
PUBLISHED
  → STAFFED            (auto: recalculate_project_staffing, когда мест ≥ team_size)
STAFFED
  → PUBLISHED          (auto: если accepted < team_size после отзыва заявки)
```

### Project.status — Initiative-проект (source_type = INITIATIVE)

```
[создание] → ON_MODERATION    (сразу при создании)
  → PUBLISHED                 (moderate_project, decision="approve")
  → REVISION_REQUESTED        (moderate_project, decision="reject") ← unique!
    → ON_MODERATION           (submit_project_for_moderation, студент дорабатывает)
      → ... (цикл повторяется)
```

---

*Связанные файлы: [00-actor-goal-model.md](00-actor-goal-model.md) · [UC-04-Submit-Application.md](UC-04-Submit-Application.md)*
