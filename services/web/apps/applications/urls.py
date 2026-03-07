from django.urls import path

from .views import ApplicationListCreateAPIView, ApplicationRetrieveUpdateDestroyAPIView

urlpatterns = [
    path("", ApplicationListCreateAPIView.as_view(), name="application-list"),
    path("<int:pk>/", ApplicationRetrieveUpdateDestroyAPIView.as_view(), name="application-detail"),
]
