# Technical Overview

- [Key Technologies](#key-technologies)
- [Request operations](#request-operations)
- [Authentication](#authentication)
- [Authorization](#authorization)
- [Running In Hosted Environments](#running-in-hosted-environments)
  - [ECS](#ecs)

## Key Technologies

The API is written in Python, utilizing Connexion as the web application
framework (with Flask serving as the backend for Connexion). The API is
described in the OpenAPI Specification format in the file
[openapi.yaml](/api/openapi.yaml).

SQLAlchemy is the ORM, with migrations driven by Alembic. pydantic is used in
many spots for parsing data (and often serializing it to json or plain
dictionaries). Where pydantic is not used, plain Python dataclasses are
generally preferred.

- [OpenAPI Specification][oas-docs]
- [Connexion][connexion-home] ([source code][connexion-src])
- [SQLAlchemy][sqlalchemy-home] ([source code][sqlalchemy-src])
- [Alembic][alembic-home] ([source code](alembic-src))
- [pydantic][pydantic-home] ([source code][pydantic-src])
- [poetry](https://python-poetry.org/docs/) - Python dependency management

[oas-docs]: http://spec.openapis.org/oas/v3.0.3
[oas-swagger-docs]: https://swagger.io/docs/specification/about/

[connexion-home]: https://connexion.readthedocs.io/en/latest/
[connexion-src]: https://github.com/zalando/connexion

[pydantic-home]:https://pydantic-docs.helpmanual.io/
[pydantic-src]: https://github.com/samuelcolvin/pydantic/

[sqlalchemy-home]: https://www.sqlalchemy.org/
[sqlalchemy-src]: https://github.com/sqlalchemy/sqlalchemy

[alembic-home]: https://alembic.sqlalchemy.org/en/latest/

## Request operations

- OpenAPI spec (`openapi.yml`) defines API interface: routes, requests, responses, etc.
- Connexion connects routes to handlers via `operationId` property on a route
    - Connexion will run OAS validations before reaching handler
    - Connexion will run authentication code and set user in the request context
    - The route handlers live in the route folder
      [app/api/route/](/app/api/route/), with the `operationId` pointing
      to the specific module and function
- Handlers check if user in request context is authorized to perform the action
  the request represents
- Handlers use pydantic models to parse request bodies and construct response data
- Connexion will run OAS validations on response format from handler

## Authentication

Authentication methods are defined in the `securitySchemes` block in
`openapi.yaml`. A particular security scheme is enabled for a route via a
`security` block on that route.

Connexion runs the authentication before passing the request to the route
handler. In the `api_key` security scheme, the `X-Auth` points to the
function that is run to do the authentication.

## Authorization
n/a - Specific user authorization is not yet implemented for this API.

### Database diagram
n/a - Database diagrams are not yet available for this application.