from . import views
from django.urls import path, include

urlpatterns = [
    path(
        "ontologies/",
        views.OntologyViewSet.as_view({"get": "list", "post": "create"}),
        name="ontology-list",
    ),
    path(
        "ontologies/<int:pk>/",
        views.OntologyViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="ontology-detail",
    ),
    path(
        "terms/",
        views.TermViewSet.as_view({"get": "list", "post": "create"}),
        name="term-list",
    ),
    path(
        "terms/<int:pk>/",
        views.TermViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="term-detail",
    ),
    path("search/", views.SearchView.as_view(), name="search-terms"),
]
