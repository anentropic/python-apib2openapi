import json
from pathlib import Path

import pytest
from hypothesis import given, note
from hypothesis_jsonschema import from_schema

from apib2openapi.models import OpenAPI3Document


def openapi3_spec():
    """
    This is a JSON Schema representation of the OpenAPI 3.0 spec, taken from:
    https://github.com/OAI/OpenAPI-Specification/blob/master/schemas/v3.0/schema.json
    """
    path = Path(__file__).parent / Path(f"fixtures/openapi3/schema.json")
    with open(path) as f:
        return json.load(f)


@pytest.mark.skip(
    reason="https://github.com/Zac-HD/hypothesis-jsonschema/issues/32"
)
@given(example_schema=from_schema(openapi3_spec()))
def test_openapi3_example_schemas(example_schema):
    """
    Simple round-trip test... if we instantiate an `OpenAPI3Document`
    model from the example schema, and then marshall it back to a dict (i.e.
    prior to re-export schema as a yaml file again)... do the dicts match?
    """
    note(example_schema)
    doc = OpenAPI3Document.parse_obj(example_schema)
    serialized = doc.dict(by_alias=True, exclude_unset=True)
    assert serialized == example_schema
