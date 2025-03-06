# Use TypedDict to model parameters to service methods

- Status: accepted
- Deciders: @chouinar @zelgadis
- Date: 2023-01-05

## Context and Problem Statement

We want to design a pattern of writing API code that provides appropriate levels of static and runtime type safety when dealing with API request bodies and parameters to service methods while minimizing code duplication if possible.

In `apiflask`, [Marshmallow](https://marshmallow.readthedocs.io/en/stable/) schemas are used to perform runtime validation of the JSON request body of incoming requests. However, the resulting object that is loaded from the JSON is still a plain `dict`, which loses all its type information.

Consider the following example:

```python
class UserSchema(apiflask.Schema):
    id = fields.UUID(dump_only=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)

@apiflask.post("/users")
@marshmallow.input(UserSchema)
@marshmallow.output(UserSchema)
def users_post(create_user_params: dict):
    user_service.create_user(create_user_params)

# in module user_service.py
def create_user(create_user_params: dict):
    # do stuff
```

The `user_service.create_user` service method takes a dictionary of create_user_params, which has no static or run-time type safety. It makes it more difficult to implement `create_user` since the IDE won't be able to autocomplete properties for `create_user_params`, and it is more difficult to test as well since tests will need to construct appropriately shaped dictionaries to pass into `create_user`. Furthermore, runtime type safety only applies to web requests. Other uses of the service, such as within a background job context, won't have any type safety at all.

An additional challenge is that related services often have similar, but not identical schemas. For example, many REST resources often support a `PATCH` endpoint that allows a client to update a subset of the resource's fields. In the `PATCH` context, "required" fields that can't be null are no longer required.

So to continue the user example, suppose we store the create user parameters into a dataclass and add a `post_load` hook to the marshmallow schema to convert the dictionary to the dataclass object.

```python
@dataclasses.dataclass
class UserParams:
    first_name: str
    last_name: str

class UserSchema(apiflask.Schema):
    ...

    @marshmallow.post_load
    def make_user(self, data: dict, kwargs: dict) -> UserParams:
        return UserParams(**data)
```

Then we can change the type of `create_user_params` to the `UserParams` class, which adds a lot of type safety.

```python
@marshmallow.output(UserSchema)
def users_post(create_user_params: UserParams):
    user_service.create_user(create_user_params)

# in module user_service.py
def create_user(create_user_params: UserParams):
    # do stuff
```

But we can't reuse the same `UserParams` for the `PATCH` endpoint, since the `PATCH` endpoint allows partial updates. Thus, the following code won't work, since the `UserParams` dataclass requires all fields to be not `None`.

```python
@user_blueprint.patch("/v1/users/<uuid:user_id>")
# Allow partial updates. partial=true means requests that are missing
# required fields will not be rejected.
# https://marshmallow.readthedocs.io/en/stable/quickstart.html#partial-loading
@user_blueprint.input(user_schemas.UserSchema(partial=True))
@user_blueprint.output(user_schemas.UserSchema)
def users_patch(user_id: str, patch_user_params: UserParams):
    user_service.patch_user(patch_user_params)
```

We want a better pattern that solves these issues.

## Decision Drivers

Goals:

1. Type safety
2. Good developer experience (IDE auto-completion, info about variables in the object)
3. Simple to understand
4. Minimize code duplication
   1. Between API schema and service method (e.g. "API schema for POST /v1/users" and the "create user" service method)
   2. Between related service methods (e.g. "create user" and "patch user")

## Decision Outcome

Chosen option: "[option 1]", because [justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | … | comes out best (see below)].

## Considered Options

### Data type for service parameters

We considered the following data type options for representing parameters to service methods.

- **Plain dict** – With plain dictionaries, the only type safety that is provided is what is provided at runtime by Marshmallow. In order to get type safety in both API and background job contexts, we'd want to re-run Marshmallow validation within service methods, [as suggested in this PR comment](https://github.com/navapbc/template-application-flask/pull/51#discussion_r1054846653). The problem is that this still doesn't support static type checking, so IDE autocomplete won't be available and activities like writing tests may also become more challenging.
- **[Python dataclass](https://docs.python.org/3/library/dataclasses.html)** – This provides static type safety and additionally provides some basic runtime type safety. For example, when constructing an instance of a dataclass by unpacking a dictionary, the dataclass will throw a `TypeError` if unknown keys are passed into the constructor:

    ```python
    @dataclass
    class Foo:
        bar: str

    d = {"typo": "baz"}
    Foo(**d) # raises a TypeError
    ```

- **[Pydantic class](https://docs.pydantic.dev/)** – Pydantic is a competing framework to Marshmallow that provides static and runtime type safety similar to Marshmallow but stores the results of deserialization into objects rather than leaving them as dictionaries. Additionally, Pydantic helps keep track of which object attributes were explicitly set, which helps distinguish between attributes that were set as `None` and attributes that weren't set at all. This is useful for implementing `PATCH` endpoints. The problem is that we don't want to have two frameworks that do effectively the same thing. If we wanted to use Pydantic, we should consider switching to the [fastapi framework](https://fastapi.tiangolo.com/) which uses Pydantic natively.
- **[TypedDict](https://docs.python.org/3/library/typing.html#typing.TypedDict)** – This keeps the code structurally as simple as a plain dict, but adds static type safety by defining the structure of the dict.

### Reusing definitions for patch requests

In attempting to minimize code duplication between defining parameters for "create" service methods and "patch" service methods, we considered the following options:

- **Use a single dataclass for create params, where all fields can be `None`, and define a generic `PatchParams` class that is generic on the create params type and has an extra `fields_to_patch` attribute to keep track of which fields were actually set.**

    ```python
    @dataclass
    class CreateUserParams:
        first_name: str | None
        last_name: str | None

    T = TypeVar("T")
    @dataclass
    class PatchParams(Generic[T]):
        resource: T
        fields_to_patch: list[str]
    ```

    The problem with this is that it's not possible to tell from looking at the `CreateUserParams` class which fields are required or not, as they all need to be able to be able to be `None` for the `PATCH` request to work. Also, developers would be forced to add `assert create_user_params.first_name is not None` in method calls to pass type checking. An alternative would be to define a `missing` sentinal value that is separate from `None`, which can be used to distinguish between `None`, [as suggested by @zelgadis in this PR comment](https://github.com/navapbc/template-application-flask/pull/51#discussion_r1053891320).

- **Use separate dataclasses for create and patch params, where all fields can have the type `Missing`, indicating that the field was unset.**

    ```python
    class Missing:
        pass
    missing = Missing()

    @dataclass
    class CreateUserParams:
        first_name: str
        last_name: str

    @dataclass
    class PatchUserParams:
        first_name: str | Missing = missing
        last_name: str | Missing = missing
    ```

    Having separate classes is simpler to understand and is more rigorous from a type safety perspective, but there's code duplication.

- **Use separate `TypedDict` types for create and patch params, and use `TypedDict`'s `total=False` feature to support fields not being set at all**

    ```python
    class CreateUserParams(TypedDict):
        first_name: str
        last_name: str

    class PatchUserParams(TypedDict, total=False):
        first_name: str
        last_name: str
    ```

    This is the simplest to understand and supports type safety, at the cost of some code duplication.

## Links

- [PR implementing this decision](https://github.com/navapbc/template-application-flask/pull/57)
- [Discussion exploring options on the PR for switching from `connexion` to `apiflask`](https://github.com/navapbc/template-application-flask/pull/51#discussion_r1053724252)
- [Concurrent PR exploring dataclass option](https://github.com/navapbc/template-application-flask/pull/56)
- [PR exploring using TypedDict instead of dataclass](https://github.com/navapbc/template-application-flask/pull/62)
