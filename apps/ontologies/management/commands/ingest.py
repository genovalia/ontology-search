from django.core.management.base import BaseCommand, CommandError
from apps.ontologies.models import Ontology, Term
from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, DCTERMS, RDFS
import requests


def load_owl_from_url(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        raise CommandError(f"Failed to fetch the ontology from {url}: {e}")
    return response.text


def parse_ontology(text_data: str, format="application/rdf+xml"):
    graph = Graph()
    graph.parse(data=text_data, format=format)
    return graph


def create_ontologies(graph: Graph):
    result = []
    for subject in graph.subjects(RDF.type, OWL.Ontology):
        uri = str(subject)
        label = ""

        for s, p, o in graph.triples((subject, DCTERMS.title, None)):
            label = str(o)
            break

        ontology, created = Ontology.objects.get_or_create(
            uri=uri, defaults={"label": label}
        )
        if created:
            print(f"Created ontology: {ontology.label} ({ontology.uri})")
        else:
            print(f"Ontology already exists: {ontology.label} ({ontology.uri})")
        result.append(ontology)
    return result


def create_terms(graph: Graph, ontology: Ontology):
    count = 0
    for subject in graph.subjects(RDF.type, OWL.Class):

        uri = str(subject)
        label = ""
        definition = ""

        for s, p, o in graph.triples((subject, RDFS.label, None)):
            label = str(o)
            break

        for s, p, o in graph.triples(
            (subject, URIRef("http://purl.obolibrary.org/obo/IAO_0000115"), None)
        ):
            definition = str(o)
            break

        term, created = Term.objects.get_or_create(
            uri=uri,
            ontology=ontology,
            label=label,
            definition=definition,
        )

        count += 1
        if count % 100 == 0:
            print(f"Processed {count} terms...")
    print(f"Created {count} terms for ontology: {ontology.label} ({ontology.uri})")


def assign_subclasses(graph: Graph):
    term_count = 0
    subclass_count = 0
    for term in Term.objects.filter(subClassOf__isnull=True):
        term_count += 1
        subclasses = list(graph.objects(URIRef(term.uri), RDFS.subClassOf))
        if subclasses:
            subclass_count += len(subclasses)
            term.subClassOf = [str(subclass) for subclass in subclasses]
            term.save()
        if term_count % 100 == 0:
            print(f"Processed {term_count} terms...")

    print(f"Assigned {subclass_count} subclasses to {term_count} terms.")


class Command(BaseCommand):
    help = "Import an ontology from a URL"

    def add_arguments(self, parser):
        parser.add_argument(
            "url",
            type=str,
            help="The URL of the ontology to import",
        )
        parser.add_argument(
            "--format",
            type=str,
            default="application/rdf+xml",
            help="The format of the ontology (default: application/rdf+xml)",
        )

    def handle(self, *args, **options):
        print(f"Fetching ontology from {options['url']}...")
        text_data = load_owl_from_url(options["url"])
        print("Parsing ontology...")
        graph = parse_ontology(text_data, format=options["format"])
        print("Creating ontologies...")
        ontologies = create_ontologies(graph)
        for ontology in ontologies:
            print(f"Creating terms for ontology: {ontology.label} ({ontology.uri})")
            create_terms(graph, ontology)
        print("Assigning subclasses to terms...")
        assign_subclasses(graph)
