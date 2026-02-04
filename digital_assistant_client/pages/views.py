from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
import django

def home(request):
    """Главная страница"""
    context = {
        'current_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'technologies': [
            'Python', 'Django', 'HTML5', 'CSS3', 
            'JavaScript', 'Bootstrap', 'SQLite'
        ],
        'project_name': 'Цифровой Ассистент Студента'
    }
    return render(request, 'pages/home.html', context)

def about(request):
    """Страница "О проекте" """
    context = {
        'django_version': django.get_version(),
        'start_date': 'Январь 2025',
    }
    return render(request, 'pages/about.html', context)

def contact(request):
    """Контактная страница"""
    return render(request, 'pages/contact.html', {})

def test_page(request):
    return HttpResponse("""
    <h1>Тестовая страница</h1>
    <p>Django успешно работает!</p>
    <p>Папка настроек: core/</p>
    <p>Приложение для страниц: pages/</p>
    <a href="/">На главную</a>
    """)
