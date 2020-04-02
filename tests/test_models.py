from pathlib import Path

import pytest
import yaml

from apib2openapi.models import OpenAPI3Document


@pytest.fixture(
    scope="module",
    params=[
        "api-with-examples.yaml",
        "callback-example.yaml",
        "link-example.yaml",
        "petstore-expanded.yaml",
        "petstore.yaml",
        "uspto.yaml",
    ]
)
def example_schema(request):
    path = Path(__file__).parent / Path(f"fixtures/openapi3/{request.param}")
    with open(path) as f:
        yield yaml.load(f.read(), Loader=yaml.FullLoader)


def test_openapi3_example_schemas(example_schema):
    """
    Simple round-trip test... if we instantiate an `OpenAPI3Document`
    model from the example schema, and then marshall it back to a dict (i.e.
    prior to re-export schema as a yaml file again)... do the dicts match?
    """
    doc = OpenAPI3Document.parse_obj(example_schema)
    serialized = doc.dict(by_alias=True, exclude_unset=True)
    assert serialized == example_schema
