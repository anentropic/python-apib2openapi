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
    doc = {
        'openapi': OPEN_API_VERSION,
        'title': bp['name'],
        'description': bp['description'],
        'version': api_version,  # e.g. git hash
        'servers': [
            {'url': metadata_value(bp, 'HOST')},
        ],
        'paths': [
            # have to do some hack with tags to reproduce the blueprint's
            # Resource Group > Resource structure, and build support into UI
            # ...or generate separate OpenAPI schema per Resource Group
        ]
    }
