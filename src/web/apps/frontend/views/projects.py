import hashlib
import json
import logging
from collections import Counter, defaultdict
from typing import cast

from apps.applications.models import Application, ApplicationStatus
from apps.frontend.decorators import customer_required, student_required
from apps.frontend.forms import InitiativeProjectForm, ProjectFrontendForm
from apps.frontend.forms.projects import _TAGS_MAX
from apps.projects.models import Project, ProjectSourceType, ProjectStatus
from apps.projects.normalization import normalize_technology_tag, normalize_technology_tags
from apps.projects.transitions import submit_project_for_moderation
from apps.projects.utils import collect_all_tags
from apps.users.models import UserRole
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError

logger = logging.getLogger(__name__)

_LOGIN_URL = reverse_lazy("frontend:auth")

PAGE_SIZE        = 9
RECOMMENDED_COUNT = 6
_RECS_CACHE_TTL   = 300   # seconds
_FACULTY_CACHE_TTL = 3600  # seconds

_LOCKED_STATUSES    = {ProjectStatus.PUBLISHED, ProjectStatus.STAFFED, ProjectStatus.ARCHIVED}
_DELETABLE_STATUSES = {ProjectStatus.DRAFT, ProjectStatus.REJECTED}
_CUSTOMER_STATUSES  = (
    ProjectStatus.DRAFT,
    ProjectStatus.ON_MODERATION,
    ProjectStatus.PUBLISHED,
    ProjectStatus.STAFFED,
    ProjectStatus.REJECTED,
)

_PUB_TYPE_RU = {
    "ARTICLE":    "Статья",
    "BOOK":       "Книга",
    "PREPRINT":   "Препринт",
    "CHAPTER":    "Глава в книге",
    "CONFERENCE": "Конференция",
    "THESIS":     "Диссертация",
    "OTHER":      "Прочее",
}


@login_required(login_url=_LOGIN_URL)
def project_list(request):
    _is_student = False
    if request.user.is_authenticated:
        try:
            _role = request.user.profile.role
        except Exception:
            _role = ""
        if _role == UserRole.CUSTOMER:
            return _customer_project_list(request)
        _is_student = _role == UserRole.STUDENT

    q                  = request.GET.get("q", "").strip()
    tech_tags_filter   = request.GET.getlist("tech_tags")
    team_size_filter   = request.GET.get("team_size", "").strip()
    source_type_filter = request.GET.get("source_type", "").strip()
    page_number        = request.GET.get("page", 1)

    queryset = Project.objects.filter(status=ProjectStatus.PUBLISHED).select_related("owner")

    if q:
        queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))

    for tag in tech_tags_filter:
        normalized_tag = normalize_technology_tag(tag)
        if normalized_tag:
            queryset = queryset.filter(
                Q(technologies__normalized_name=normalized_tag)
                | Q(tech_tags__contains=[normalized_tag])
            ).distinct()

    if team_size_filter:
        try:
            queryset = queryset.filter(team_size=int(team_size_filter))
        except ValueError:
            pass

    if source_type_filter and source_type_filter in {
        ProjectSourceType.SUPERVISOR,
        ProjectSourceType.INITIATIVE,
        ProjectSourceType.EPP,
        ProjectSourceType.MANUAL,
    }:
        queryset = queryset.filter(source_type=source_type_filter)

    queryset  = queryset.order_by("-created_at")
    paginator = Paginator(queryset, PAGE_SIZE)
    page_obj  = paginator.get_page(page_number)

    is_filtered = bool(q or tech_tags_filter or team_size_filter or source_type_filter)
    visible_ids = [p.id for p in page_obj.object_list]

    user_applications = {}
    if request.user.is_authenticated:
        apps = Application.objects.filter(
            applicant=request.user,
            project_id__in=visible_ids,
        ).values("project_id", "status")
        user_applications = {a["project_id"]: a["status"] for a in apps}

    all_tags = collect_all_tags()

    user_interests: list[str] = []
    if _is_student:
        try:
            user_interests = normalize_technology_tags(request.user.profile.interests or [])
        except Exception:
            pass

    context = {
        "page_obj":           page_obj,
        "query":              q,
        "tech_tags_filter":   tech_tags_filter,
        "team_size_filter":   team_size_filter,
        "source_type_filter": source_type_filter,
        "user_applications":  user_applications,
        "all_tags":           all_tags,
        "is_filtered":        is_filtered,
        "user_interests":     user_interests,
        "ApplicationStatus":  ApplicationStatus,
        "ProjectStatus":      ProjectStatus,
        "ProjectSourceType":  ProjectSourceType,
    }

    show_recs_tab         = False
    rec_projects          = []
    rec_reasons           = {}
    rec_mode              = None
    has_interests         = False
    rec_user_applications = {}

    show_applications_tab  = False
    my_applications        = []
    app_counts             = {}
    my_initiative_projects = []
    suggested_interests: list[str] = []

    if _is_student:
        show_recs_tab = True
        try:
            rec_projects, rec_reasons, rec_mode = _get_recommendations(request)
        except Exception:
            logger.warning("_get_recommendations failed in project_list", exc_info=True)
        has_interests = bool(getattr(getattr(request.user, "profile", None), "interests", None))
        rec_ids = [p.id for p in rec_projects]
        if rec_ids:
            rec_apps = Application.objects.filter(
                applicant=request.user,
                project_id__in=rec_ids,
            ).values("project_id", "status")
            rec_user_applications = {a["project_id"]: a["status"] for a in rec_apps}

        show_applications_tab = True
        my_applications = list(
            Application.objects.filter(applicant=request.user)
            .select_related("project", "project__owner")
            .order_by("-created_at")
        )
        app_counts = {
            "total":     len(my_applications),
            "submitted": sum(1 for a in my_applications if a.status == ApplicationStatus.SUBMITTED),
            "accepted":  sum(1 for a in my_applications if a.status == ApplicationStatus.ACCEPTED),
            "rejected":  sum(1 for a in my_applications if a.status == ApplicationStatus.REJECTED),
        }
        my_initiative_projects = list(
            Project.objects.filter(
                owner=request.user, source_type=ProjectSourceType.INITIATIVE
            ).order_by("-created_at")
        )

        if not has_interests:
            fav_ids      = list(request.user.profile.favorite_project_ids)
            applied_ids  = [a.project_id for a in my_applications]
            activity_ids = list({*fav_ids, *applied_ids})[:20]
            if activity_ids:
                tag_counts: Counter = Counter()
                for _p in Project.objects.filter(pk__in=activity_ids).only("tech_tags"):
                    for _tag in (_p.tech_tags or []):
                        tag_counts[_tag] += 1
                suggested_interests = [t for t, _ in tag_counts.most_common(6)]

    show_bookmarks_tab         = False
    bookmarked_ids             = set()
    bookmark_page_obj          = None
    bookmark_user_applications = {}

    if request.user.is_authenticated:
        show_bookmarks_tab = True
        fav_ids        = list(request.user.profile.favorite_project_ids)
        bookmarked_ids = set(fav_ids)
        if fav_ids:
            bm_queryset = (
                Project.objects.filter(pk__in=fav_ids).select_related("owner").order_by("-pk")
            )
            bookmark_page_number = request.GET.get("bookmark_page", 1)
            bm_paginator         = Paginator(bm_queryset, PAGE_SIZE)
            bookmark_page_obj    = bm_paginator.get_page(bookmark_page_number)
            bm_apps = Application.objects.filter(
                applicant=request.user,
                project_id__in=fav_ids,
            ).values("project_id", "status")
            bookmark_user_applications = {a["project_id"]: a["status"] for a in bm_apps}

    context.update({
        "show_recs_tab":              show_recs_tab,
        "rec_projects":               rec_projects,
        "rec_reasons":                rec_reasons,
        "rec_mode":                   rec_mode,
        "has_interests":              has_interests,
        "rec_user_applications":      rec_user_applications,
        "show_bookmarks_tab":         show_bookmarks_tab,
        "bookmarked_ids":             bookmarked_ids,
        "bookmark_page_obj":          bookmark_page_obj,
        "bookmark_user_applications": bookmark_user_applications,
        "show_applications_tab":      show_applications_tab,
        "my_applications":            my_applications,
        "app_counts":                 app_counts,
        "my_initiative_projects":     my_initiative_projects if _is_student else [],
        "suggested_interests":        suggested_interests,
    })

    if request.headers.get("HX-Request") and request.headers.get("HX-Target") == "projects-section":
        return render(request, "frontend/partials/projects_grid.html", context)

    return render(request, "frontend/project_list.html", context)


def _get_recommendations(request):
    from apps.recs.services import recommend_projects

    interests = []
    if request.user.is_authenticated:
        try:
            interests = list(request.user.profile.interests or [])
        except Exception:
            pass

    if interests:
        interests_hash = hashlib.sha256(json.dumps(sorted(interests)).encode()).hexdigest()[:16]
        cache_key      = f"recs:u{request.user.pk}:{interests_hash}"

        cached = cache.get(cache_key)
        if cached is not None:
            cached_mode, raw_items = cached
            pk_list       = [item["pk"] for item in raw_items]
            project_by_pk = {
                p.pk: p for p in Project.objects.filter(pk__in=pk_list).select_related("owner")
            }
            projects = [
                project_by_pk[item["pk"]] for item in raw_items if item["pk"] in project_by_pk
            ]
            reasons = {
                item["pk"]: item["reason"] for item in raw_items if item["pk"] in project_by_pk
            }
            return projects, reasons, cached_mode

        try:
            mode, items = recommend_projects(interests, limit=RECOMMENDED_COUNT)
            projects  = [cast(Project, item["project"]) for item in items]
            reasons   = {cast(Project, item["project"]).pk: item["reason"] for item in items}
            raw_items = [
                {"pk": cast(Project, item["project"]).pk, "reason": item["reason"]}
                for item in items
            ]
            cache.set(cache_key, (mode, raw_items), timeout=_RECS_CACHE_TTL)
            return projects, reasons, mode
        except Exception:
            logger.warning("recs.service failed, falling back to latest projects", exc_info=True)

    projects = list(
        Project.objects.filter(status=ProjectStatus.PUBLISHED)
        .select_related("owner")
        .order_by("-created_at")[:RECOMMENDED_COUNT]
    )
    return projects, {}, None


def _customer_project_list(request):
    page_number   = request.GET.get("page", 1)
    status_filter = request.GET.get("status", "").strip()

    base_qs  = Project.objects.filter(owner=request.user)
    queryset = base_qs.order_by("-created_at")

    if status_filter:
        queryset = queryset.filter(status=status_filter)

    counts = base_qs.aggregate(
        **{s: Count("pk", filter=Q(status=s)) for s in _CUSTOMER_STATUSES}
    )

    paginator = Paginator(queryset, PAGE_SIZE)
    page_obj  = paginator.get_page(page_number)

    app_agg = Application.objects.filter(project__owner=request.user).aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status=ApplicationStatus.SUBMITTED)),
        accepted=Count("id", filter=Q(status=ApplicationStatus.ACCEPTED)),
    )

    projects_with_pending = list(
        Project.objects.filter(owner=request.user)
        .annotate(
            pending_count=Count(
                "applications",
                filter=Q(applications__status=ApplicationStatus.SUBMITTED),
            ),
        )
        .filter(pending_count__gt=0)
        .order_by("-pending_count")[:8]
    )

    published_qs     = list(base_qs.filter(status=ProjectStatus.PUBLISHED))
    spots_left_total = sum(
        max(0, p.team_size - p.accepted_participants_count) for p in published_qs
    )

    dashboard = {
        "total_apps":            app_agg["total"] or 0,
        "pending_apps":          app_agg["pending"] or 0,
        "accepted_apps":         app_agg["accepted"] or 0,
        "active_projects":       counts.get(ProjectStatus.PUBLISHED, 0),
        "on_moderation":         counts.get(ProjectStatus.ON_MODERATION, 0),
        "spots_left_total":      spots_left_total,
        "projects_with_pending": projects_with_pending,
    }

    articles     = _fetch_faculty_publications() or _get_sample_articles()
    staff        = _fetch_faculty_staff() or _get_sample_staff()
    graph_source = articles if any(a.get("authors") for a in articles) else _get_sample_articles()
    graph_nodes, graph_edges = _build_graph_data(graph_source)

    article_years = sorted(
        {a["year"] for a in articles if a.get("year")},
        reverse=True,
    )
    article_directions = sorted(
        {a["direction"] for a in articles if a.get("direction")},
    )

    return render(request, "frontend/my_projects.html", {
        "page_obj":           page_obj,
        "status_filter":      status_filter,
        "ProjectStatus":      ProjectStatus,
        "ApplicationStatus":  ApplicationStatus,
        "counts":             counts,
        "total_count":        base_qs.count(),
        "dashboard":          dashboard,
        "sample_articles":    articles,
        "article_years":      article_years,
        "article_directions": article_directions,
        "sample_staff":       staff,
        "graph_nodes_json":   json.dumps(graph_nodes, ensure_ascii=False),
        "graph_edges_json":   json.dumps(graph_edges, ensure_ascii=False),
    })


def _fetch_faculty_publications(limit: int = 8) -> list[dict]:
    from apps.faculty.models import FacultyAuthorship, FacultyPublication

    cache_key = f"faculty:pubs:{limit}"
    cached    = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        pubs = list(
            FacultyPublication.objects
            .prefetch_related(
                Prefetch(
                    "authorships",
                    queryset=FacultyAuthorship.objects.order_by("position"),
                )
            )
            .order_by("-year", "-id")[:limit]
        )
        articles = []
        for pub in pubs:
            authors = [a.display_name for a in pub.authorships.all() if a.display_name]
            articles.append({
                "title":     pub.title,
                "authors":   authors,
                "venue":     "",
                "year":      pub.year,
                "doi_url":   pub.url or "",
                "keywords":  [],
                "direction": _PUB_TYPE_RU.get(pub.publication_type, pub.publication_type),
            })
        if articles:
            cache.set(cache_key, articles, timeout=_FACULTY_CACHE_TTL)
        return articles
    except Exception:
        logger.warning("faculty ORM publications query failed", exc_info=True)
        return []


def _fetch_faculty_staff(limit: int = 8) -> list[dict]:
    from apps.faculty.models import FacultyPerson

    cache_key = f"faculty:staff:{limit}"
    cached    = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        persons = list(
            FacultyPerson.objects
            .filter(is_stale=False)
            .order_by("-publications_total")[:limit]
        )
        staff = []
        for p in persons:
            position = ""
            if isinstance(p.positions, list) and p.positions:
                first = p.positions[0]
                if isinstance(first, dict):
                    position = str(first.get("position") or first.get("title") or "").strip()
            staff.append({
                "name":           p.full_name,
                "position":       position or p.primary_unit,
                "department":     p.primary_unit,
                "research_areas": list(p.interests)[:3] if p.interests else [],
                "works_count":    p.publications_total,
                "profile_url":    p.source_profile_url,
            })
        if staff:
            cache.set(cache_key, staff, timeout=_FACULTY_CACHE_TTL)
        return staff
    except Exception:
        logger.warning("faculty ORM staff query failed", exc_info=True)
        return []


def _get_sample_articles():
    return [
        {
            "title": "Recommender Systems for Project-Student Matching in Higher Education",
            "authors": ["Иванов А. В.", "Смирнова Е. Н."],
            "venue": "Educational Data Mining. 2023. Vol. 15. P. 112–128",
            "year": 2023,
            "doi_url": "https://doi.org/10.5555/example1",
            "keywords": ["recommender systems", "higher education", "student matching"],
            "direction": "Компьютерные науки",
        },
        {
            "title": "Graph-Based Knowledge Representation for Academic Collaboration Networks",
            "authors": ["Петров И. С."],
            "venue": "Journal of Information Science. 2022. Vol. 48. No. 3. P. 341–359",
            "year": 2022,
            "doi_url": "https://doi.org/10.5555/example2",
            "keywords": ["knowledge graphs", "Neo4j", "academic networks"],
            "direction": "Информационные системы",
        },
        {
            "title": "Machine Learning Approaches to Automated Project Supervision Assignment",
            "authors": ["Козлова М. Д.", "Фёдоров П. А.", "Белов С. Г."],
            "venue": "Artificial Intelligence in Education. 2023. Vol. 9. P. 78–94",
            "year": 2023,
            "doi_url": "https://doi.org/10.5555/example3",
            "keywords": ["machine learning", "project supervision", "automation"],
            "direction": "Компьютерные науки",
        },
        {
            "title": "Модели компетентностного подхода в управлении студенческими проектами",
            "authors": ["Волкова Т. И."],
            "venue": "Вопросы образования. 2022. № 2. С. 88–109",
            "year": 2022,
            "doi_url": "https://doi.org/10.5555/example4",
            "keywords": ["компетентностный подход", "студенческие проекты", "управление"],
            "direction": "Педагогика",
        },
        {
            "title": "Natural Language Processing for Research Topic Extraction in University Repositories",  # noqa: E501
            "authors": ["Морозов Д. К.", "Новикова А. Л."],
            "venue": "Information Processing Letters. 2021. Vol. 168. P. 106–119",
            "year": 2021,
            "doi_url": "https://doi.org/10.5555/example5",
            "keywords": ["NLP", "topic extraction", "university repositories"],
            "direction": "Компьютерные науки",
        },
    ]


def _get_sample_staff():
    return [
        {
            "name": "Иванов Александр Викторович",
            "position": "Профессор",
            "department": "Факультет компьютерных наук",
            "research_areas": ["Machine Learning", "Recommender Systems"],
            "works_count": 58,
            "profile_url": "https://www.hse.ru/org/persons/",
        },
        {
            "name": "Смирнова Елена Николаевна",
            "position": "Доцент",
            "department": "Школа анализа данных",
            "research_areas": ["Natural Language Processing", "Text Mining"],
            "works_count": 34,
            "profile_url": "https://www.hse.ru/org/persons/",
        },
        {
            "name": "Петров Игорь Сергеевич",
            "position": "Старший научный сотрудник",
            "department": "Институт проблем передачи информации",
            "research_areas": ["Knowledge Graphs", "Graph Databases", "Neo4j"],
            "works_count": 27,
            "profile_url": "https://www.hse.ru/org/persons/",
        },
        {
            "name": "Козлова Мария Дмитриевна",
            "position": "Доцент",
            "department": "Департамент больших данных и информационного поиска",
            "research_areas": ["Deep Learning", "Computer Vision"],
            "works_count": 41,
            "profile_url": "https://www.hse.ru/org/persons/",
        },
    ]


def _build_graph_data(articles):
    author_articles: dict[str, list[str]] = defaultdict(list)
    for article in articles:
        for author in article.get("authors", []):
            author_articles[author].append(article.get("title", ""))

    nodes = []
    author_index: dict[str, int] = {}
    for i, (author, titles) in enumerate(author_articles.items()):
        author_index[author] = i
        nodes.append({
            "id":    i,
            "label": author,
            "value": len(titles),
            "title": f"{author}<br/>Публикаций в выборке: {len(titles)}",
        })

    edge_counts: dict[tuple[int, int], int]       = defaultdict(int)
    edge_titles: dict[tuple[int, int], list[str]] = defaultdict(list)
    for article in articles:
        authors = article.get("authors", [])
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                a   = author_index[authors[i]]
                b   = author_index[authors[j]]
                key = (min(a, b), max(a, b))
                edge_counts[key] += 1
                edge_titles[key].append(article.get("title", ""))

    edges = []
    for key, weight in edge_counts.items():
        a, b = key
        tooltip_lines = "<br/>".join(
            t[:60] + ("…" if len(t) > 60 else "") for t in edge_titles[key]
        )
        edges.append({
            "from":  a,
            "to":    b,
            "value": weight,
            "title": f"Совместных статей: {weight}<br/>{tooltip_lines}",
        })

    return nodes, edges


@login_required(login_url=_LOGIN_URL)
def project_detail(request, pk):
    project = get_object_or_404(Project.objects.select_related("owner"), pk=pk)

    is_owner  = request.user.is_authenticated and project.owner == request.user
    is_public = project.status in ProjectStatus.catalog_values()

    if not is_public and not is_owner and not request.user.is_staff:
        raise PermissionDenied

    application = None
    if request.user.is_authenticated and not is_owner:
        application = Application.objects.filter(
            project=project,
            applicant=request.user,
        ).first()

    spots_left = max(0, project.team_size - project.accepted_participants_count)

    return render(request, "frontend/project_detail.html", {
        "project":           project,
        "application":       application,
        "is_owner":          is_owner,
        "spots_left":        spots_left,
        "ApplicationStatus": ApplicationStatus,
        "ProjectStatus":     ProjectStatus,
    })


@login_required(login_url=_LOGIN_URL)
@customer_required
def project_create(request):
    if request.method == "POST":
        form = ProjectFrontendForm(request.POST)
        if form.is_valid():
            project = Project.objects.create(
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                tech_tags=form.cleaned_data["tech_tags_raw"],
                team_size=form.cleaned_data["team_size"],
                owner=request.user,
                status=ProjectStatus.DRAFT,
            )
            messages.success(request, "Проект создан!")
            return redirect("frontend:project_detail", pk=project.pk)
    else:
        form = ProjectFrontendForm()

    return render(request, "frontend/project_form.html", {
        "form":        form,
        "is_create":   True,
        "tags_initial": "",
    })


@login_required(login_url=_LOGIN_URL)
def project_edit(request, pk):
    project = get_object_or_404(Project.objects.select_related("owner"), pk=pk)

    if project.owner != request.user and not request.user.is_staff:
        raise PermissionDenied

    if project.status in _LOCKED_STATUSES:
        messages.error(
            request,
            f"Редактирование недоступно — проект имеет статус «{project.get_status_display()}».",
        )
        return redirect("frontend:project_detail", pk=project.pk)

    if request.method == "POST":
        form = ProjectFrontendForm(request.POST)
        if form.is_valid():
            project.title       = form.cleaned_data["title"]
            project.description = form.cleaned_data["description"]
            project.tech_tags   = form.cleaned_data["tech_tags_raw"]
            project.team_size   = form.cleaned_data["team_size"]
            project.save(
                update_fields=["title", "description", "tech_tags", "team_size", "updated_at"]
            )
            messages.success(request, "Проект сохранён!")
            return redirect("frontend:project_detail", pk=project.pk)
        tags_initial = request.POST.get("tech_tags_raw", "")
    else:
        tags_initial = ", ".join(project.tech_tags) if project.tech_tags else ""
        form = ProjectFrontendForm(initial={
            "title":         project.title,
            "description":   project.description,
            "tech_tags_raw": tags_initial,
            "team_size":     project.team_size,
        })

    return render(request, "frontend/project_form.html", {
        "form":        form,
        "project":     project,
        "is_create":   False,
        "tags_initial": tags_initial,
    })


@require_POST
@login_required(login_url=_LOGIN_URL)
def project_submit_moderation(request, pk):
    project = get_object_or_404(Project, pk=pk)
    try:
        submit_project_for_moderation(project, request.user)
        messages.success(request, "Проект отправлен на модерацию!")
    except (DRFPermissionDenied, DRFValidationError):
        messages.error(request, "Нельзя отправить проект на модерацию в текущем статусе.")
    return redirect("frontend:project_detail", pk=project.pk)


@require_POST
@login_required(login_url=_LOGIN_URL)
def project_delete(request, pk):
    project = get_object_or_404(Project.objects.select_related("owner"), pk=pk)

    if project.owner != request.user and not request.user.is_staff:
        raise PermissionDenied

    if project.status not in _DELETABLE_STATUSES:
        messages.error(
            request, f"Нельзя удалить проект со статусом «{project.get_status_display()}»."
        )
        return redirect("frontend:project_detail", pk=project.pk)

    title = project.title
    project.delete()
    messages.success(request, f"Проект «{title}» удалён.")
    return redirect("frontend:project_list")


@login_required(login_url=_LOGIN_URL)
def recommendations_view(request):
    return redirect(reverse("frontend:project_list") + "?tab=recs")


@require_POST
@login_required(login_url=_LOGIN_URL)
def toggle_bookmark(request, pk):
    get_object_or_404(Project, pk=pk)
    profile   = request.user.profile
    favorites = list(profile.favorite_project_ids)

    if pk in favorites:
        favorites.remove(pk)
        bookmarked = False
    else:
        favorites.append(pk)
        bookmarked = True

    profile.set_favorite_project_ids(favorites)
    profile.save(update_fields=["favorite_project_ids"])
    return JsonResponse({"bookmarked": bookmarked})


@login_required(login_url=_LOGIN_URL)
@student_required
def initiative_project_create(request):
    if request.method == "POST":
        form = InitiativeProjectForm(request.POST)
        if form.is_valid():
            project = Project.objects.create(
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                tech_tags=form.cleaned_data["tech_tags_raw"],
                team_size=form.cleaned_data["team_size"],
                supervisor_name=form.cleaned_data["supervisor_name"],
                owner=request.user,
                source_type=ProjectSourceType.INITIATIVE,
                status=ProjectStatus.ON_MODERATION,
            )
            messages.success(request, "Проект отправлен на проверку!")
            return redirect("frontend:project_detail", pk=project.pk)
        tags_initial = request.POST.get("tech_tags_raw", "")
    else:
        tags_initial = ""
        form = InitiativeProjectForm()

    return render(request, "frontend/initiative_form.html", {
        "form":        form,
        "tags_initial": tags_initial,
    })
