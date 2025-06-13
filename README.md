# Ontology API Search

- deploy with `docker compose up`
- exec into the container with `docker compose exec -it backend /bin/bash`
- import FoodOn into the database with `python manage.py ingest https://raw.githubusercontent.com/FoodOntology/foodon/master/foodon.owl`
- Be patient. The ontology will quickly be downloaded, then slowly parsed. Finally, its content will be ingested and indexed into the database.

- Go to `http://localhost:8080/swagger-ui/` and try out the search endpoint.
- You can connect to the admin interface at `http://localhost:8080/admin/` (or the swagger-ui interface at the top-right) with the credentials:
  - username: `admin`
  - password: `password`
- You can edit a term by setting it as favorite or adding weight to it, and it will come first in a query.


Next steps:
- there are a couple of known issues:
  - the search endpoint does not support pagination yet
  - favorites and weights are all or nothing
  - ontology-wide weighting is not yet implemented (to recommand certain ontologies over others)
  - some values of subClassOf are not URIs, and editing a term with a non-URI subClassOf value will prevent saving it.
  - subClassOf values are URIs and not objects.


Performance seems good but was tested on a powerful machine. There's an index on terms for uri+ ontology. Maybe one for searchable fields would be useful.
