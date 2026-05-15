# Use Case Documentation

> **System:** Цифровой Студенческий Ассистент  
> **Methodology:** Cockburn "Writing Effective Use Cases"  
> **Last updated:** 2026-05-09 · **15/15 UC fully dressed**

---

## Навигация

### Мета-документы

| Файл | Содержимое |
|---|---|
| [00-actor-goal-model.md](00-actor-goal-model.md) | Actor-Goal List · границы системы · backbone · приоритеты |
| [00-business-rules.md](00-business-rules.md) | Все бизнес-правила BR-APP-*, BR-PRJ-*, BR-MOD-*, BR-STA-*, BR-USR-* |

### Use Cases — статус разработки

| UC | Название | Актор | Уровень | Статус |
|---|---|---|---|---|
| [UC-04](UC-04-Submit-Application.md) | Подать заявку на проект | Студент | 🌊 | ✅ Fully Dressed |
| [UC-09](UC-09-Create-Project.md) | Создать проект | Преподаватель | 🌊 | ✅ Fully Dressed |
| [UC-10](UC-10-Submit-For-Moderation.md) | Отправить проект на модерацию | Преподаватель | 🌊 | ✅ Fully Dressed |
| [UC-11](UC-11-Review-Applications.md) | Рассмотреть заявки на проект | Преподаватель | 🌊 | ✅ Fully Dressed |
| [UC-12](UC-12-Moderate-Project.md) | Промодерировать проект | ЦППРП | 🌊 | ✅ Fully Dressed |
| [UC-06](UC-06-Propose-Initiative-Project.md) | Предложить инициативный проект | Студент | 🌊 | ✅ Fully Dressed |
| [UC-03](UC-03-Find-Project.md) | Найти проект | Студент | 🌊 | ✅ Fully Dressed |
| [UC-01](UC-01-Register.md) | Зарегистрироваться и верифицировать email | Студент | 🌊 | ✅ Fully Dressed |
| [UC-02](UC-02-Login.md) | Авторизоваться в системе | Все | 🐟 | ✅ Fully Dressed |
| [UC-05](UC-05-Withdraw-Application.md) | Отозвать заявку на проект | Студент | 🌊 | ✅ Fully Dressed |
| [UC-07](UC-07-Bookmark-Project.md) | Сохранить/убрать проект из закладок | Студент | 🌊 | ✅ Fully Dressed |
| [UC-08](UC-08-Edit-Profile.md) | Редактировать профиль | Все | 🌊 | ✅ Fully Dressed |
| [UC-13](UC-13-Manage-Deadlines.md) | Управлять дедлайнами платформы | ЦППРП | 🌊 | ✅ Fully Dressed |
| [UC-14](UC-14-Manage-Templates.md) | Управлять шаблонами документов | ЦППРП | 🌊 | ✅ Fully Dressed |
| [UC-15](UC-15-Export-Data.md) | Экспортировать данные платформы | ЦППРП | 🌊 | ✅ Fully Dressed |

---

## Backbone

```
UC-09 Создать проект
  ↓
UC-10 Отправить на модерацию
  ↓
UC-12 Промодерировать → PUBLISHED
  ↓
UC-03 Найти проект (Студент)
  ↓
UC-04 Подать заявку ← центральная цель студента
  ↓
UC-11 Рассмотреть заявки → ACCEPTED
```

---

## Шаблон fully dressed UC

```markdown
# UC-NN: Название

| Атрибут | Значение |
|---|---|
| Scope | Цифровой Студенческий Ассистент |
| Level | 🌊 / 🐟 / ☁️ + label |
| Primary Actor | ... |
| Supporting Actors | ... |
| Revision | x.x · YYYY-MM-DD |

## Цель в контексте
## Стейкхолдеры и интересы
## Предусловия
## Триггер
## Гарантии (Минимальная / Успеха)
## Основной сценарий успеха (таблица: Шаг | Кто | Действие)
## Расширения (NX. Условие → шаги → исход)
## Перечень технологических и пользовательских вариаций
## Бизнес-правила (ссылки на 00-business-rules.md)
## Переходы состояний
## Связанные Use Cases
```

---

## Соглашения

- **Нумерация расширений:** `Na.` — номер шага + буква; `Na.N.` — шаг внутри расширения
- **Ссылки на BR:** `[BR-APP-01](00-business-rules.md#заявки-applications)` — inline в тексте шагов
- **Исходы расширений:** явно указываем одно из: «Продолжить с шага N», «Сценарий завершается», «Вернуться к шагу N»
- **Уровни целей:** ☁️ Summary · 🌊 User Goal · 🐟 Subfunction · 🐚 Too Low (не документируем)
