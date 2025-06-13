from django.contrib.postgres.search import SearchVector

from rest_framework import viewsets
from rest_framework.views import APIView, Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.ontologies import models
from . import serializers


class OntologyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    queryset = models.Ontology.objects.all()
    serializer_class = serializers.OntologySerializer


class TermViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    queryset = models.Term.objects.all()
    serializer_class = serializers.TermSerializer


class SearchView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        operation_id="Search Terms",
        description="Search for terms by their URI, label, or definition using a full-text search.",
        parameters=[
            OpenApiParameter(
                name="query",
                type=str,
                description="The search query string to match against term URIs, labels, or definitions.",
                required=True,
            ),
        ],
        responses={
            200: serializers.TermSerializer(many=True),
            400: {"description": "Bad Request"},
        },
    )
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("query", "")
        if not query:
            return Response(
                {"error": "Query parameter 'query' is required."}, status=400
            )

        terms = models.Term.objects.annotate(
            search=SearchVector("uri", "label", "definition"),
        ).filter(search=query)

        terms.order_by("is_favorite", "weight", "label")

        serializer = serializers.TermSerializer(terms, many=True)
        return Response(serializer.data)
