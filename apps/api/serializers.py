from apps.ontologies import models
from rest_framework import serializers


class OntologySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Ontology
        fields = ("uri", "label")


class TermSerializer(serializers.ModelSerializer):
    ontology = OntologySerializer(read_only=True)

    class Meta:
        model = models.Term
        fields = (
            "uri",
            "label",
            "definition",
            "ontology",
            "subClassOf",
            "weight",
            "is_favorite",
        )
        read_only_fields = ("uri", "ontology")
