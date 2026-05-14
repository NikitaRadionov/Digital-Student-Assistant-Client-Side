"""
seed_demo — заполняет БД демонстрационными данными для показа на защите.

Удаляет все существующие проекты и создаёт 5 реалистичных проектов
в статусе PUBLISHED с заполненными полями.

Использование:
    uv run python src/web/manage.py seed_demo --settings=config.settings.dev
"""

import datetime
import os

from apps.projects.models import Project, ProjectSourceType, ProjectStatus
from apps.users.models import UserProfile, UserRole
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEMO_PASSWORD = os.getenv("DSA_SEED_USER_PASSWORD", "Demo1234!")

DEMO_PROJECTS = [
    {
        "title": "Цифровой ассистент студента: рекомендательная система проектов",
        "description": (
            "Разработка веб-платформы для автоматизации поиска и подбора проектов ВКР/КП "
            "для студентов НИУ ВШЭ. Система анализирует интересы студента и историю "
            "взаимодействий, формирует персонализированные рекомендации на основе "
            "коллаборативной фильтрации. Бэкенд реализован на Django REST Framework, "
            "фронтенд — серверный рендеринг с HTMX и Tailwind CSS."
        ),
        "tech_tags": ["python", "django", "postgresql", "redis", "docker", "htmx", "tailwindcss"],
        "team_size": 2,
        "study_course": 3,
        "education_program": "Программная инженерия",
        "work_format": "Смешанный",
        "hours_per_week": 8,
        "is_paid": False,
        "application_deadline": datetime.date(2026, 6, 15),
        "selection_criteria": (
            "Опыт работы с Django или любым другим веб-фреймворком. "
            "Базовые знания SQL. Желание разбираться в алгоритмах рекомендаций."
        ),
        "supervisor_name": "Иванова Екатерина Сергеевна",
        "supervisor_department": "Департамент программной инженерии",
        "supervisor_email": "ekaterina.ivanova@hse.ru",
    },
    {
        "title": "ML-сервис классификации медицинских изображений для телемедицины",
        "description": (
            "Проект направлен на создание микросервиса классификации рентгеновских снимков "
            "лёгких с помощью сверточных нейронных сетей. Сервис интегрируется с "
            "телемедицинской платформой через REST API и поддерживает потоковую обработку "
            "изображений. В рамках проекта предстоит собрать датасет, обучить модель на "
            "базе ResNet/EfficientNet, развернуть инференс на GPU-кластере."
        ),
        "tech_tags": ["python", "pytorch", "fastapi", "docker", "kubernetes", "postgresql"],
        "team_size": 3,
        "study_course": 3,
        "education_program": "Прикладная математика и информатика",
        "work_format": "Дистанционный",
        "hours_per_week": 10,
        "is_paid": True,
        "application_deadline": datetime.date(2026, 6, 1),
        "selection_criteria": (
            "Знание Python на уровне не ниже intermediate. "
            "Базовое понимание свёрточных нейронных сетей (CNN). "
            "Опыт работы с PyTorch или TensorFlow будет преимуществом."
        ),
        "supervisor_name": "Петров Алексей Николаевич",
        "supervisor_department": "Лаборатория искусственного интеллекта",
        "supervisor_email": "alexey.petrov@hse.ru",
    },
    {
        "title": "Система мониторинга и аналитики для городской транспортной сети",
        "description": (
            "Разработка дашборда реального времени для отслеживания загруженности "
            "городского транспорта на основе открытых данных МГТС и API Яндекс.Транспорта. "
            "Система агрегирует данные с помощью Apache Kafka, хранит в ClickHouse, "
            "визуализирует через Grafana и собственный веб-интерфейс. "
            "Предусмотрен модуль прогнозирования пиковой нагрузки."
        ),
        "tech_tags": ["python", "kafka", "clickhouse", "grafana", "react", "fastapi", "docker"],
        "team_size": 3,
        "study_course": 4,
        "education_program": "Компьютерные науки",
        "work_format": "Гибридный",
        "hours_per_week": 12,
        "is_paid": True,
        "application_deadline": datetime.date(2026, 5, 30),
        "selection_criteria": (
            "Знание основ распределённых систем. "
            "Опыт работы с реляционными или колоночными СУБД. "
            "Знание Python, желателен опыт с потоковой обработкой данных."
        ),
        "supervisor_name": "Смирнова Ольга Владимировна",
        "supervisor_department": "Школа анализа данных",
        "supervisor_email": "olga.smirnova@hse.ru",
    },
    {
        "title": "Мобильное приложение для управления личными финансами с AI-советником",
        "description": (
            "Создание кроссплатформенного мобильного приложения на Flutter, которое "
            "автоматически категоризирует расходы, строит прогнозы бюджета и даёт "
            "персональные советы через LLM-ассистента. Бэкенд на Django обеспечивает "
            "синхронизацию данных и интеграцию с банковскими API (Open Banking). "
            "ML-модуль предсказывает аномалии расходов."
        ),
        "tech_tags": ["flutter", "dart", "python", "django", "openai", "postgresql", "redis"],
        "team_size": 2,
        "study_course": 3,
        "education_program": "Программная инженерия",
        "work_format": "Дистанционный",
        "hours_per_week": 8,
        "is_paid": False,
        "application_deadline": datetime.date(2026, 6, 10),
        "selection_criteria": (
            "Базовые навыки разработки мобильных приложений (Flutter или React Native). "
            "Понимание REST API. Интерес к финтех-проектам."
        ),
        "supervisor_name": "Козлов Дмитрий Андреевич",
        "supervisor_department": "Департамент информационных технологий",
        "supervisor_email": "dmitry.kozlov@hse.ru",
    },
    {
        "title": "Платформа для автоматизированного код-ревью с использованием LLM",
        "description": (
            "Проект предполагает разработку инструмента, интегрирующегося в GitLab CI/CD "
            "и выполняющего автоматическое код-ревью с помощью больших языковых моделей "
            "(GPT-4o / Claude). Система анализирует pull request'ы, выявляет потенциальные "
            "баги, нарушения code style и предлагает рефакторинги. "
            "Включает веб-дашборд с историей ревью и метриками качества кода."
        ),
        "tech_tags": ["python", "fastapi", "gitlab", "openai", "docker", "vue.js", "postgresql"],
        "team_size": 2,
        "study_course": 3,
        "education_program": "Программная инженерия",
        "work_format": "Дистанционный",
        "hours_per_week": 10,
        "is_paid": True,
        "application_deadline": datetime.date(2026, 6, 20),
        "selection_criteria": (
            "Опыт работы с Git и понимание процессов CI/CD. "
            "Знание Python. Опыт работы с API LLM (OpenAI, Anthropic) будет преимуществом."
        ),
        "supervisor_name": "Новикова Анастасия Игоревна",
        "supervisor_department": "Центр разработки программного обеспечения",
        "supervisor_email": "anastasia.novikova@hse.ru",
    },
]


class Command(BaseCommand):
    help = "Seed demo projects for presentation. Clears existing projects first."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-clear",
            action="store_true",
            help="Do not delete existing projects before seeding.",
        )

    def handle(self, *args, **options):
        if not options["no_clear"]:
            deleted, _ = Project.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing project(s)."))

        # Создаём владельца-заказчика для демо-проектов
        owner, created = User.objects.get_or_create(
            username="demo_supervisor",
            defaults={
                "email": "demo.supervisor@hse.ru",
                "first_name": "Демо",
                "last_name": "Научрук",
                "is_active": True,
            },
        )
        if created or not owner.has_usable_password():
            owner.set_password(DEMO_PASSWORD)
            owner.save(update_fields=["password"])

        UserProfile.objects.get_or_create(
            user=owner,
            defaults={"role": UserRole.CUSTOMER},
        )

        # Создаём демо-студента
        student, created = User.objects.get_or_create(
            username="demo_student",
            defaults={
                "email": "demo.student@edu.hse.ru",
                "first_name": "Демо",
                "last_name": "Студент",
                "is_active": True,
            },
        )
        if created or not student.has_usable_password():
            student.set_password(DEMO_PASSWORD)
            student.save(update_fields=["password"])

        UserProfile.objects.get_or_create(
            user=student,
            defaults={"role": UserRole.STUDENT},
        )

        # Создаём модератора ЦППРП
        moderator, created = User.objects.get_or_create(
            username="demo_moderator",
            defaults={
                "email": "demo.moderator@hse.ru",
                "first_name": "Демо",
                "last_name": "Модератор",
                "is_active": True,
                "is_staff": True,
            },
        )
        if created or not moderator.has_usable_password():
            moderator.set_password(DEMO_PASSWORD)
            moderator.save(update_fields=["password"])
        elif not moderator.is_staff:
            moderator.is_staff = True
            moderator.save(update_fields=["is_staff"])

        UserProfile.objects.get_or_create(
            user=moderator,
            defaults={"role": UserRole.CPPRP},
        )

        for data in DEMO_PROJECTS:
            project, created = Project.objects.get_or_create(
                title=data["title"],
                defaults={
                    "description": data["description"],
                    "tech_tags": data["tech_tags"],
                    "team_size": data["team_size"],
                    "study_course": data["study_course"],
                    "education_program": data["education_program"],
                    "work_format": data["work_format"],
                    "hours_per_week": data["hours_per_week"],
                    "is_paid": data["is_paid"],
                    "application_deadline": data["application_deadline"],
                    "selection_criteria": data["selection_criteria"],
                    "supervisor_name": data["supervisor_name"],
                    "supervisor_department": data["supervisor_department"],
                    "supervisor_email": data["supervisor_email"],
                    "owner": owner,
                    "status": ProjectStatus.PUBLISHED,
                    "source_type": ProjectSourceType.MANUAL,
                },
            )
            verb = "Created" if created else "Already exists"
            self.stdout.write(f"  {verb}: «{project.title[:60]}»")

        self.stdout.write(self.style.SUCCESS("\nDemo data ready!"))
        self.stdout.write(f"  Студент:   demo.student@edu.hse.ru  / {DEMO_PASSWORD}")
        self.stdout.write(f"  Заказчик:  demo.supervisor@hse.ru   / {DEMO_PASSWORD}")
        self.stdout.write(f"  Модератор: demo.moderator@hse.ru    / {DEMO_PASSWORD}")
