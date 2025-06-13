from django.contrib import admin
from . import models


@admin.register(models.Ontology)
class OntologyAdmin(admin.ModelAdmin):
    list_display = ("label", "uri", "created_at")
    search_fields = ("label", "uri")
    ordering = ("-created_at",)


@admin.register(models.Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("label", "ontology", "is_favorite", "weight", "created_at")
    search_fields = ("label", "uri")
    ordering = ("uri",)
    list_filter = ("ontology", "is_favorite")
