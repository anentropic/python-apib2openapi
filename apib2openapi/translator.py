"""
openapi: 3.0.0
info:
  title: Sample API
  description: Optional multiline or single-line description in [CommonMark](http://commonmark.org/help/) or HTML.
  version: 0.1.9
servers:
  - url: http://api.example.com/v1
    description: Optional server description, e.g. Main (production) server
  - url: http://staging-api.example.com
    description: Optional server description, e.g. Internal staging server for testing
paths:
  /pets:
    get:
      summary: List all pets
      operationId: listPets
      tags:
        - pets
"""

OPEN_API_VERSION = '3.0.0'


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
