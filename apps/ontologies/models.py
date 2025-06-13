from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    weight = models.FloatField(default=1.0, blank=True, null=True)

    class Meta:
        abstract = True


class Ontology(BaseModel):
    uri = models.URLField(primary_key=True)
    label = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label or self.uri


class Term(BaseModel):
    uri = models.URLField(primary_key=True)
    ontology = models.ForeignKey(
        Ontology,
        related_name="terms",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    label = models.CharField(max_length=255, blank=True, null=True)
    definition = models.TextField(blank=True, null=True)
    subClassOf = models.ForeignKey(
        "self",
        related_name="subClasses",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    weight = models.FloatField(default=1.0, blank=True, null=True)
    is_favorite = models.BooleanField(default=False)

    def __str__(self):
        return self.label or self.uri
