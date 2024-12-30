# Keep generated OpenAPI YAML specification file in source control

* Status: accepted
* Deciders: @chouinar @sawyerh
* Date: 2023-02-22

## Context and Problem Statement

With the switch from Connexion to APIFlask (see [Connection replacement ADR](./0001-connexion-replacement.md)), the code-first approach to defining the API specification meant that the `openapi.yml` file was no longer needed. This caused multiple engineers to be confused as to why the file still existed in source control. This ADR decides how to eliminate that confusion.

## Considered Options

* Remove openapi.yml from source control since the `/docs` endpoint is generated from schemas defined in code and no longer relies on the openapi.yml file
* Keep openapi.yml in source control, and automatically keep it in sync with the code
* Keep openapi.yml in source control, and have a CI check that ensures that it is kept in sync with the code

## Decision Outcome

We chose to keep the openapi.yml file in source control because we want changes to the API to be called out explicitly so that developers do not accidentally make backwards-incompatible changes to the API as part of a code change. This is particularly important since the API spec is now implicit as the OpenAPI specification is automatically generated from the code.

We chose to keep the openapi.yml file in sync with the API application automatically using a [CI workflow that generates the OpenAPI and pushes and changes to the PR branch](../../.github/workflows/ci-openapi.yml). This reduces the amount of manual work required by the engineer compared to a CI check that only checks for diffs but does not make the change. That said, we don't feel strongly about this decision so are open to changes in the future.

To minimize developer confusion, we chose to rename the `openapi.yml` file to `openapi.generated.yml` to clearly indicate that it is a generated file and not something that the developer should manually adjust.
