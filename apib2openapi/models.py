import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import (
    BaseModel as PydanticBaseModel,
    conint,
    constr,
    EmailStr,
    Field,
    HttpUrl,
    PositiveInt,
    root_validator,
    validator,
)

# TODO: replace all Any with Optional[object] ?

# TODO: support extensions


class BaseModel(PydanticBaseModel):
    class Config:
        use_enum_values = True
        allow_mutation = False
        # TODO: auto CamelCase?
        # also... remember to use `model.dict(by_alias=True)`


class Contact(BaseModel):
    name: Optional[str]
    url: HttpUrl
    email: EmailStr


class License(BaseModel):
    name: str
    url: HttpUrl


class Info(BaseModel):
    title: str
    description: Optional[str]
    termsOfService: Optional[str]
    contact: Optional[Contact]
    license: Optional[License]
    version: str


class ServerVariable(BaseModel):
    enum: Optional[Set[str]]  # TODO: StrEnum?
    default: str
    description: Optional[str]


class Server(BaseModel):
    url: str  # NO VALIDATION: MAY be relative, MAY have { } for var substitutions
    description: Optional[str]
    variables: Optional[Dict[str, ServerVariable]]


class ExternalDocumentation(BaseModel):
    description: Optional[str]
    url: HttpUrl


class Discriminator(BaseModel):
    propertyName: str
    mapping: Optional[Dict[str, str]]


class XMLObj(BaseModel):
    name: Optional[str]
    namespace: Optional[HttpUrl]
    prefix: Optional[str]
    attribute: bool = False
    wrapped: bool = False  # takes effect only when defined alongside type being array (outside the items)


SchemaOrRef = Union["Schema", "Reference"]


class Schema(BaseModel):
    class Config:
        # hopefully this allows these fields to remain unset?
        fields = {
            "type_": {"alias": "type"},
            "not_": {"alias": "not"},
            "format_": {"alias": "format"},
        }

    title: Optional[str]
    multipleOf: Optional[PositiveInt]
    maximum: Optional[float]
    exclusiveMaximum: bool = False
    minimum: float
    exclusiveMinimum: bool = False
    maxLength: Optional[PositiveInt]
    minLength: Optional[conint(ge=0)]
    pattern: Optional[str]
    maxItems: Optional[conint(ge=0)]
    minItems: Optional[conint(ge=0)]
    uniqueItems: bool = False
    maxProperties: Optional[conint(ge=0)]
    minProperties: Optional[conint(ge=0)]
    required: Optional[Set[str]]
    enum: Optional[Set[Any]]

    type_: Optional[str]
    allOf: Optional[List[SchemaOrRef]]
    oneOf: Optional[List[SchemaOrRef]]
    anyOf: Optional[List[SchemaOrRef]]
    not_: Optional[List[SchemaOrRef]]
    items: Optional[SchemaOrRef]
    properties: Optional[Dict[str, Union["PropertySchema", "Reference"]]]
    additionalProperties: Union[bool, SchemaOrRef] = True
    description: Optional[str]
    format_: Optional[str]
    default: Any

    nullable: bool = False
    discriminator: Optional[Discriminator]
    externalDocs: Optional[ExternalDocumentation]
    example: Any
    deprecated: bool = False

    @validator("required")
    def check_required(self, v):
        assert len(v) > 0, "`required` must be non-empty if present"
        return v

    @validator("enum")
    def check_enum(self, v):
        assert len(v) > 0, "`enum` must be non-empty if present"
        return v

    @root_validator
    def check_items(self, values):
        if values.get("type") == "array":
            assert values.get("items"), "`items` must be present when `type='array'`"
        return values

    @root_validator
    def check_discriminator(self, values):
        # The discriminator object is legal only when using one of the composite keywords oneOf, anyOf, allOf.
        if not any(key in values for key in {"oneOf", "anyOf", "allOf"}):
            raise ValueError(
                "`discriminator` is legal only when using one of the composite keywords `oneOf`, `anyOf`, `allOf`."
            )
        return values


class PropertySchema(Schema):
    readOnly: bool = False
    writeOnly: bool = False
    xml: Optional[XMLObj]


class Reference(BaseModel):
    ref: str = Field(..., alias="$ref")


class Example(BaseModel):
    summary: Optional[str]
    description: Optional[str]
    value: Any
    externalValue: Optional[HttpUrl]

    @root_validator
    def check_value(cls, values):
        if values.get("value") and values.get("externalValue"):
            raise ValueError("`value` and `externalValue` are mutually-exclusive")
        return values


class Encoding(BaseModel):
    contentType: Optional[str]
    headers: Optional[Dict[str, Union['Header', Reference]]]
    style: Optional[str]
    explode: bool = False  # TODO True when style=form
    # TODO


class MediaType(BaseModel):
    schema: Optional[Union[Schema, Reference]]
    example: Any
    examples: Optional[Dict[str, Union[Example, Reference]]]
    encoding: Optional[Dict[str, Encoding]]

    @root_validator
    def check_examples(cls, values):
        if values.get("example") and values.get("examples"):
            raise ValueError("`example` and `examples` are mutually-exclusive")
        return values


class In(str, Enum):
    QUERY = "query"
    HEADER = "header"
    PATH = "path"
    COOKIE = "cookie"


class Style(str, Enum):
    MATRIX = "matrix"
    LABEL = "label"
    FORM = "form"
    SIMPLE = "simple"
    SPACE_DELIMITED = "spaceDelimited"
    PIPE_DELIMITED = "pipeDelimited"
    DEEP_OBJECT = "deepObject"


IN_STYLES_MAP = {
    In.QUERY: {
        Style.FORM,
        Style.SPACE_DELIMITED,
        Style.PIPE_DELIMITED,
        Style.DEEP_OBJECT,
    },
    In.HEADER: {
        Style.SIMPLE,
    },
    In.PATH: {
        Style.MATRIX,
        Style.LABEL,
        Style.SIMPLE,
    },
    In.COOKIE: {
        Style.FORM,
    }
}

IN_STYLE_DEFAULTS = {
    In.QUERY: Style.FORM,
    In.HEADER: Style.SIMPLE,
    In.PATH: Style.SIMPLE,
    In.COOKIE: Style.FORM,
}


class Header(BaseModel):
    description: Optional[str]
    required: bool = False
    deprecated: bool = False
    allowEmptyValue: bool = False

    style: Optional[Style]
    explode: bool = False
    allowReserved: bool = False
    schema: Optional[Union[Schema, Reference]]
    example: Any  # TODO: Optional[object] ?
    examples: Optional[Dict[str, Union[Example, Reference]]]

    content: Optional[Dict[str, MediaType]]

    @root_validator
    def check_allow_empty_value(cls, values):
        if values.get("allowEmptyValue"):
            raise ValueError("allowEmptyValue=True is not valid for Header")
        return values

    @root_validator
    def check_style_and_explode(cls, values):
        style = values.get("style")
        if style:
            assert style in IN_STYLES_MAP[In.HEADER]
        else:
            values["style"] = IN_STYLE_DEFAULTS[In.HEADER]
        return values

    @root_validator
    def check_allow_reserved(cls, values):
        if values.get("allowReserved"):
            raise ValueError("allowReserved=True is not valid for Header")
        return values

    @root_validator
    def check_examples(cls, values):
        if values.get("example") and values.get("examples"):
            raise ValueError("`example` and `examples` are mutually-exclusive")
        return values

    @validator("content")
    def check_content(cls, v):
        assert len(v) == 1
        return v


class Parameter(BaseModel):
    name: str
    in_: In = Field(..., alias="in")
    description: Optional[str]
    required: bool = False
    deprecated: bool = False
    allowEmptyValue: bool = False

    style: Optional[Style]
    explode: bool = False
    allowReserved: bool = False
    schema: Optional[Union[Schema, Reference]]
    example: Any
    examples: Optional[Dict[str, Union[Example, Reference]]]

    content: Optional[Dict[str, MediaType]]

    @root_validator
    def check_required(cls, values):
        if values["in_"] is In.PATH:
            assert values['required'] is True
        return values

    @root_validator
    def check_allow_empty_value(cls, values):
        if values.get("allowEmptyValue") and values["in_"] is not In.QUERY:
            raise ValueError("allowEmptyValue=True is only valid for in='query'")
        return values

    @root_validator
    def check_style_and_explode(cls, values):
        style = values.get("style")
        if style:
            assert style in IN_STYLES_MAP[values["in_"]]
        else:
            values["style"] = IN_STYLE_DEFAULTS[values["in_"]]

        if "explode" not in values and values.get("style") is Style.FORM:
            values["explode"] = True

        return values

    @root_validator
    def check_allow_reserved(cls, values):
        if values.get("allowReserved") and values["in_"] is not In.QUERY:
            raise ValueError("allowReserved=True is only valid for in='query'")
        return values

    @root_validator
    def check_examples(cls, values):
        if values.get("example") and values.get("examples"):
            raise ValueError("`example` and `examples` are mutually-exclusive")
        return values

    @validator("content")
    def check_content(cls, v):
        assert len(v) == 1
        return v


class RequestBody(BaseModel):
    description: Optional[str]
    content: Dict[str, MediaType]
    required: bool = False


class Link(BaseModel):
    operationRef: Optional[str]
    operationId: Optional[str]
    parameters: Optional[Dict[str, Any]]
    requestBody: Optional[Any]
    description: Optional[str]
    server: Optional[Server]

    @root_validator
    def check_operation(cls, values):
        if values.get("operationRef") and values.get("operationId"):
            raise ValueError(
                "`operationRef` and `operationId` are mutually-exclusive"
            )
        return values


class Response(BaseModel):
    description: Optional[str]
    headers: Optional[Dict[str, Union[Header, Reference]]]
    content: Optional[Dict[str, MediaType]]
    links: Optional[Dict[str, Union[Link, Reference]]]


HTTP_STATUS_RE = re.compile(r"^[1-5][X0-9]{2}|default$")


class Responses(BaseModel):
    __root__: Dict[str, Union[Response, Reference]]

    @root_validator
    def check_http_status(cls, values):
        for key in values:
            if not HTTP_STATUS_RE.match(key):
                raise ValueError(f"{key} is not a valid Response key")
        return values


class Callback(BaseModel):
    __root__: Dict[str, 'PathItem']


class SecurityRequirement(BaseModel):
    __root__: Dict[str, List[str]]
    # Each name MUST correspond to a security scheme which is declared in the
    # Security Schemes under the Components Object. (TODO)


class Operation(BaseModel):
    tags: Optional[List[str]]
    summary: Optional[str]
    description: Optional[str]
    externalDocs: Optional[ExternalDocumentation]
    operationId: Optional[str]
    parameters: Optional[Set[Union[Parameter, Reference]]]
    requestBody: Optional[Union[RequestBody, Reference]]
    responses: Responses
    callbacks: Optional[Dict[str, Union[Callback, Reference]]]
    deprecated: bool = False
    security: Optional[List[SecurityRequirement]]
    servers: Optional[List[Server]]


class PathItem(BaseModel):
    ref: Optional[str] = Field(..., alias="$ref")
    summary: Optional[str]
    description: Optional[str]
    get: Optional[Operation]
    put: Optional[Operation]
    post: Optional[Operation]
    delete: Optional[Operation]
    options: Optional[Operation]
    head: Optional[Operation]
    patch: Optional[Operation]
    trace: Optional[Operation]


class Paths(BaseModel):
    __root__: Dict[str, PathItem]


class _BaseOAuthFlow(BaseModel):
    refreshUrl: Optional[HttpUrl]
    scopes: Dict[str, str]


class ImplicitOAuthFlow(BaseModel):
    authorizationUrl: HttpUrl


class AuthorizationCodeOAuthFlow(BaseModel):
    authorizationUrl: HttpUrl
    tokenUrl: HttpUrl


class PasswordOAuthFlow(BaseModel):
    tokenUrl: HttpUrl


class ClientCredentialsOAuthFlow(BaseModel):
    tokenUrl: HttpUrl


OAuthFlow = Union[
    ImplicitOAuthFlow,
    AuthorizationCodeOAuthFlow,
    PasswordOAuthFlow,
    ClientCredentialsOAuthFlow,
]


class OAuthFlows(BaseModel):
    implicit: Optional[OAuthFlow]
    password: Optional[OAuthFlow]
    clientCredentials: Optional[OAuthFlow]
    authorizationCode: Optional[OAuthFlow]


class Type_(str, Enum):
    API_KEY = "apiKey"
    HTTP = "http"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "openIdConnect"


class _BaseSecurityScheme(BaseModel):
    type_: Type_ = Field(..., alias="type")
    description: Optional[str]


class APIKeySecurityScheme(_BaseSecurityScheme):
    name: str
    in_: In

    @validator("in_")
    def check_in(cls, v):
        if v not in {In.QUERY, In.HEADER, In.COOKIE}:
            raise ValueError(f"{v} is not a valid `in` value")
        return v


class HTTPSecurityScheme(_BaseSecurityScheme):
    scheme: str
    bearerFormat: Optional[str]


class OAuth2SecurityScheme(_BaseSecurityScheme):
    flows: OAuthFlows


class OpenIDConnectSecurityScheme(_BaseSecurityScheme):
    openIdConnectUrl: HttpUrl


SecurityScheme = Union[
    APIKeySecurityScheme,
    HTTPSecurityScheme,
    OAuth2SecurityScheme,
    OpenIDConnectSecurityScheme,
]


class Components(BaseModel):
    schemas: Optional[Dict[str, Union[Schema, Reference]]]
    responses: Optional[Dict[str, Union[Response, Reference]]]
    parameters: Optional[Dict[str, Union[Parameter, Reference]]]
    examples: Optional[Dict[str, Union[Example, Reference]]]
    requestBodies: Optional[Dict[str, Union[RequestBody, Reference]]]
    headers: Optional[Dict[str, Union[Header, Reference]]]
    securitySchemes: Optional[Dict[str, Union[SecurityScheme, Reference]]]
    links: Optional[Dict[str, Union[Link, Reference]]]
    callbacks: Optional[Dict[str, Union[Callback, Reference]]]


class Tag(BaseModel):
    name: str
    description: Optional[str]
    externalDocs: Optional[ExternalDocumentation]


class OpenAPI3Document(BaseModel):
    openapi: constr(regex=r'\d+\.\d+\.\d+') = "3.0.0"
    info: Info
    servers: List[Server] = [Server(url="/")]
    paths: Paths
    components: Optional[Components]
    security: Optional[List[SecurityRequirement]]
    tags: Optional[List[Tag]]
    externalDocs: Optional[ExternalDocumentation]