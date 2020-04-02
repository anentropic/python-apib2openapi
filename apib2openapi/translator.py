import yaml

from apib2openapi.models import OpenAPI3Document


def dump(doc: OpenAPI3Document, path: str):
    serialized = doc.dict(by_alias=True, exclude_unset=True)
    with open(path, "w+") as f:
        yaml.dump(serialized, f, default_flow_style=False, sort_keys=False)


def metadata_value(bp, key):
    for item in bp['metadata']:
        if item['name'] == key:
            return item['value']


def apib_to_openapi3(bp, api_version='1.0.0'):
    pass
