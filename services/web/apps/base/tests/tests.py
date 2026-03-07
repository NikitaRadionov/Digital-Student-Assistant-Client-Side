# Create your tests here.
from django.test import Client
from django.urls import reverse


def test_home_page_ok():
    c = Client()
    r = c.get(reverse("home"))
    assert r.status_code == 200
    assert b"Digital Student Assistant Web Service" in r.content


def test_health_root_ok():
    c = Client()
    r = c.get(reverse("health-root"))
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_api_v1_health_ok():
    c = Client()
    r = c.get(reverse("api-v1-health"))
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_api_v1_projects_list_ok():
    c = Client()
    r = c.get(reverse("api-v1-project-list"))
    assert r.status_code == 200
