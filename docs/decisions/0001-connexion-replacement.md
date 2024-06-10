# Connexion Alternatives Decision Record

* Status: Approved
* Deciders: Loren Yu
* Date: 2022-09-27

Technical Story: https://github.com/navapbc/template-application-flask/issues/12

## Context and Problem Statement

This template library was built using Flask + Connexion as the API technology. We are investigating if we want to keep using Connexion, or potentially move to another Flask-wrapper API approach. Any approach we consider must make it possible to easily set up an OpenAPI/Swagger endpoint.

We aren't looking to move off of Flask at the moment as we feel that would be a much larger refactor.

## Decision Drivers

* Connexion requires you to specify an OpenAPI spec but passes the request objects as the raw JSON. We currently use Pydantic to convert this into a Python object for additional validations & for ease of use, but this effectively means we need to define any models twice.
* Defining the OpenAPI specs first instead of defining the data models in code has often been more frustrating. While one goal of doing it this way was the ability to create mock endpoints while development is ongoing, this can also be easily handled by just making the endpoint return a static response in-code.
* Connexion's defaults for validation leave a lot to be desired. While we currently override these, it adds a lot of boilerplate to this template library, and isn't immediately obvious.
* Code first is recommended by Swagger when building internal APIs that need to be built quickly: https://swagger.io/blog/api-design/design-first-or-code-first-api-development/ which is often the case for our endpoints that aren't directly exposed to users.

## Considered Options

* [APIFlask](#apiflask) **Recommended Approach**
* [Flask OpenAPI3](#flask-openapi3)
* [Flasgger](#flasgger)
* [Flask Smorest](#flask-smorest)
* [APISpec](#apispec)
* [Flask RESTX](#flask-restx)
* [APIFairy](#apifairy)

## Decision Outcome

Chosen option: "APIFlask", because it appears to be a library that has taken several lessons from the other libraries. It aims to simplify a lot of the headache with setting up and vending an OpenAPI schema while being incredibly well-documented, and very easy to configure. The documentation does a great job of explaining each component, the rationality of the default behavior, and how to adjust that behavior if needed.

### Positive Consequences <!-- optional -->

* No more writing OpenAPI specs, instead writing models once in code.
### Negative Consequences <!-- optional -->

* If we use Marshmallow-dataclass, it's a bit cumbersome to define the validation rules as they all get passed via a metadata map. A utility for generating this so you can instead do `phone_number: str = field(metadata=get_metadata(required=True, regex="...", example="..."))` would go a long way in mitigating this annoyance.

## Pros and Cons of the Options

### APIFlask

[APIFlask](https://apiflask.com/openapi/) is a framework wrapped around Flask (much like Connexion) that also leverages [marshmallow](https://github.com/marshmallow-code/marshmallow) for data models and [Flask-HTTPAuth](https://github.com/miguelgrinberg/flask-httpauth) for authentication. See [Comparison and Motivations](https://apiflask.com/comparison/) for further details on its creation and purpose.

<details>
<summary>Example implementation</summary>

```py
from datetime import date
from typing import Optional

from apiflask import APIFlask, Schema, abort
from apiflask.fields import Date, Integer, String
from apiflask.validators import Regexp

app = APIFlask(__name__)

class User(Schema):
    name: str = String(required=True)
    phone_number: str = String(
        required=True,
        validate=Regexp("^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$"),
        metadata={"example": "123-456-7890"},
    )
    date_of_birth: Optional[date] = Date(required=False)
class UserOut(User):
    user_id = Integer()


users = {
    1: User.from_dict(
        {"name": "Bob Smith", "phone_number": "123-456-7890", "date_of_birth": "2000-01-01"}
    )
}


@app.get("/user/<int:user_id>")
@app.output(UserOut)
def get_user(user_id: int):
    if user_id not in users:
        abort(404)

    return users[user_id]

@app.post("/user")
@app.input(User)
@app.output(UserOut)
def create_user(data: dict):
    user = User.from_dict(data)
    next_id = max(users.keys()) + 1
    user.user_id = next_id

    users[next_id] = user
    return user

if __name__ == "__main__":
    app.run(port=8080)
```

Alternatively, if using Marshmallow Dataclasses, you can do the following to be able to work with the schema as dataclass objects.
```py
from marshmallow_dataclass import dataclass as marshmallow_dataclass

# Same app setup and run as before, just showing the small difference

@marshmallow_dataclass
class User:
    user_id: Optional[int]
    name: str = field(metadata={"required": True})
    phone_number: str = field(metadata={
        "required": True,
        "validate":Regexp("^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$"),
        "metadata":{"example": "123-456-7890"},
    })
    date_of_birth: date = field(metadata={"required":False})

@app.post("/user")
@app.input(User.Schema)
@app.output(User.Schema)
def create_user(user: User):
    next_id = max(users.keys()) + 1
    user.user_id = next_id

    users[next_id] = user
    return user
```
</details>

* Good, because the documentation is immensely thorough, and does a great job of explaining all the customization options while providing sane defaults.
* Good, because you can [register custom error processors](https://apiflask.com/error-handling/#custom-error-response-processor) which would allow us to reuse and adapt our existing error processors - although it looks like the defaults are more sane - as all errors, not just the first get added to the error response.
* Good, because [authentication looks to be flexible](https://apiflask.com/authentication/), and allows you to define it as if you were writing the OpenAPI.
* Good, because the [API uses Marshmallow](https://apiflask.com/schema/) for its data schema, which is a [well-maintained library](https://github.com/marshmallow-code/marshmallow) - and additionally supports [Marshmallow Dataclass](https://apiflask.com/schema/#use-dataclass-as-data-schema) which is a wrapper that allows you to interact directly with dataclass objects which further improves runtime typing.
* Meh, because methods end up with several decorators, although you can [group route methods into classes](https://apiflask.com/usage/#use-class-based-views) and make them share decorators (eg. set the authentication decorator on the class).
* Bad, because APIFlask 1.0 only released in May 2022, with the first beta release about a year earlier, so the project is still somewhat young.


### Flask OpenAPI3

[Flask OpenAPI3](https://luolingchun.github.io/flask-openapi3/) is a framework wrapped around Flask (like Connexion) that uses Pydantic models for defining the OpenAPI schema.

<details>
<summary>Example implementation (note, not 100% functional)</summary>

```py
from datetime import date
from typing import Optional

from flask import abort
from flask_openapi3 import Info, OpenAPI, Tag
from pydantic import BaseModel, Field

info = Info(title="title", version="1.0.0")
tag = Tag(name="User")

app = OpenAPI(__name__)


class UserPath(BaseModel):
    user_id: int


class UserBody(BaseModel):
    name: str = Field(..., description="Name")
    phone_number: str = Field(
        ..., regex="^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$", example="123-456-7890"
    )
    date_of_birth: Optional[date]


class UserOut(UserBody):
    user_id: int


users = {
    1: UserBody.parse_obj(
        {"name": "Bob Smith", "phone_number": "123-456-7890", "date_of_birth": "2000-01-01"}
    )
}


@app.get("/user/<int:user_id>", responses={"200": UserOut}, tags=[tag])
def get_user(path: UserPath):
    if path.user_id not in users:
        abort(404)

    return users[path.user_id].dict()


@app.post("/user", responses={"200": UserOut}, tags=[tag])
def create_user(body: UserBody):
    next_id = max(users.keys()) + 1
    body.user_id = next_id

    users[next_id] = body
    return body.dict()


if __name__ == "__main__":
    app.run(port=8080)
```

</details>

* Good, because the API model definitions use Pydantic, which is a well-supported library we are already familiar with.
* Good, because the API definitions are minimal and pretty intuitive to read.
* Bad, because the documentation isn't fully detailed, and the errors that occur when trying to get the API running aren't very clear. In ~30 minutes of debugging, I hadn't figured out how to get the API to fully run.
* Bad, while it generates swagger docs, and can display example responses, it doesn't appear that you can specify example requests or parameters. This effectively makes Swagger unusable.
* Bad, because it appears that the library is primarily [maintained by one person](https://github.com/luolingchun/flask-openapi3/commits/master), and appears to still be going through early implementation fixes.

### Flasgger

[Flasgger](https://github.com/flasgger/flasgger) is a library that runs adjacent to your Flask app to vend a swagger endpoint.

Note that Flasgger has several different ways to define the schema. This specifically looked at only the approaches that defined the OpenAPI models in code, as the other approaches amount to defining your own OpenAPI schema (either as a yaml file, or as a comment on the function), which is virtually the same as how connexion works, so would provide no benefit to do.

[A tool](https://github.com/flasgger/flasgger/blob/master/examples/apispec_example.py) exists for generating the docs for Flasgger from the APISpec definitions (see that section for APISpec details), so we could combine the two if desired.

No example implementation as the ones presented in the docs didn't actually function out of the box.

* Good, because there is a lot of variety in how you set up your schema, although most require defining the JSON/YAML yourself.
* Bad, because the non-JSON/YAML approaches don't appear to be the main purpose of this API, and little documentation/examples exist regarding their usage.
* Bad, because it seems the approach for running using [Marshmallow for the schema](https://github.com/flasgger/flasgger#using-marshmallow-schemas) isn't valid anymore as the parameters that Flask takes in don't match the example. From reading various other docs, Flask seems to have had a major version update that changed it a bit in recent years, so that is likely the cause.

### Flask Smorest

[Flask Smorest](https://github.com/marshmallow-code/flask-smorest) (formerly flask-rest-api).

<details>
<summary>Example implementation (Note this uses Flask's Blueprint approach which several other approaches here also support):</summary>

```py
from datetime import date

from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort
from marshmallow import Schema, fields
from marshmallow.validate import Regexp

app = Flask(__name__)
app.config["API_TITLE"] = "Example API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
api = Api(app)


class User(Schema):
    name: str = fields.String(required=True)
    phone_number: str = fields.String(
        required=True,
        validate=Regexp("^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$"),
        metadata={"example": "123-456-7890"},
    )
    date_of_birth: date = fields.Date(required=False)


class UserOut(User):
    user_id = fields.Integer()


users = {
    1: UserOut.from_dict(
        {"name": "Bob Smith", "phone_number": "123-456-7890", "date_of_birth": date(2000, 1, 1)}
    )
}

user_blp = Blueprint("user", "user", url_prefix="/user")


@user_blp.route("/<int:user_id>")
class UserById(MethodView):
    @user_blp.response(200, UserOut)
    def get(self, user_id: int):
        if user_id not in users:
            abort(404)

        return users[user_id]


@user_blp.route("/")
class UserView(MethodView):
    @user_blp.arguments(User)
    @user_blp.response(201, UserOut)
    def post(self, data: dict):
        user = User.from_dict(data)
        next_id = max(users.keys()) + 1
        user.user_id = next_id

        users[next_id] = user
        return user


api.register_blueprint(user_blp)
if __name__ == "__main__":
    app.run(port=8080)
```

</details>

* Good, because the API uses Marshmallow for its data schema, which is a [well-maintained library](https://github.com/marshmallow-code/marshmallow) - it's in the same project.
* Good, because it is fairly straightforward and just seems to work as expected.
* Bad, because the documentation is pretty minimal beyond getting OpenAPI running. Seems like this is just an OpenAPI wrapper with no other additional features.
* Bad, because it is pretty barebones. It just sets up a swagger endpoint and does the object validation, but doesn't handle anything beyond that regarding authentication.
* Bad, because even the maintainers recognize it needs a [bit more work](https://github.com/apiflask/apiflask/discussions/14#discussioncomment-571898)

### APISpec

[APISpec](https://apispec.readthedocs.io/en/latest/index.html) is a utility for generating an OpenAPI spec from Marshmallow models, but does not actually run a swagger endpoint, or do any validation itself. It ONLY could be used for generating the spec.

<details>
<summary>Example implementation (This only generates swagger docs, but doesn't display them):</summary>

```py
from datetime import date

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import Flask, abort
from marshmallow import Schema, fields
from marshmallow.validate import Regexp

spec = APISpec(
    title="Example API",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)

spec.path

app = Flask(__name__)


class UserPath(Schema):
    user_id: fields.Int()


class User(Schema):
    name: str = fields.String(required=True)
    phone_number: str = fields.String(
        required=True,
        validate=Regexp("^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$"),
        metadata={"example": "123-456-7890"},
    )
    date_of_birth: date = fields.Date(required=False)


class UserOut(User):
    user_id = fields.Integer()


# Register the schema
spec.components.schema("UserPath", schema=UserPath)
spec.components.schema("User", schema=User)
spec.components.schema("UserOut", schema=UserOut)

users = {
    1: UserOut.from_dict(
        {"name": "Bob Smith", "phone_number": "123-456-7890", "date_of_birth": date(2000, 1, 1)}
    )
}


@app.get("/user/<int:user_id>")
def get_user(user_id: int):
    """Get User
    ---
    get:
        parameters:
        - in: path
          schema: UserPath
        responses:
          200:
             content:
                application/json:
                   schema: UserOut
    """
    if user_id not in users:
        abort(404)

    return users[user_id]


@app.post("/user")
def create_user(data: dict):
    """Create user
    ---
    post:
        content:
            application/json:
                schema: User
        responses:
            200:
                content:
                    application/json:
                        schema: UserOut


    """
    user = User.from_dict(data)
    next_id = max(users.keys()) + 1
    user.user_id = next_id

    users[next_id] = user
    return user


if __name__ == "__main__":
    with app.test_request_context():
        spec.path(view=get_user)
        spec.path(view=create_user)
        print(spec.to_yaml())
    app.run(port=8080)
```
</details>

* Good, because the API uses Marshmallow for its data schema, which is a [well-maintained library](https://github.com/marshmallow-code/marshmallow) - it's in the same project.
* Good, because it gives a lot of flexibility for defining the OpenAPI docs, [including security](https://apispec.readthedocs.io/en/latest/special_topics.html#documenting-security-schemes).
* Bad, because you still have to specify some of the OpenAPI docs as a comment on the function. The primary gain is being able to use Marshmallow to define the schema models, but the routes are still largely yaml.
* Bad, because apispec doesn't actually run the swagger docs, it just generates them. You would need to use one of the other approaches here in tandem.

### Flask RESTX

[Flask RESTX](https://github.com/python-restx/flask-restx) (a fork of Flask-RESTPlus) is a library that runs adjacent to Flask and helps standup a swagger endpoint for your app.

<details>
<summary>Example implementation</summary>

```py
from datetime import date

from flask import Flask, abort
from flask_restx import Api, Resource, fields
from marshmallow.validate import Regexp

app = Flask(__name__)
api = Api(app, version="1.0", title="Example API", description="API description")

user_namespace = api.namespace("user", description="User namespace")

user_dict = {
    "name": fields.String(required=True),
    "phone_number": fields.String(
        required=True,
        # The below 2 don't work at all - not actually using Marshmallow(?)
        validate=Regexp("^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$"),
        metadata={"example": "123-456-7890"},
    ),
    "date_of_birth": fields.Date(required=False),
}
user_model = api.model("User", user_dict)

user_out_model = api.model("UserOut", user_dict.copy() | {"user_id": fields.Integer()})


users = {
    1: ({"name": "Bob Smith", "phone_number": "123-456-7890", "date_of_birth": date(2000, 1, 1)})
}


@user_namespace.route("/<int:id>")
@user_namespace.response(404, "User not found")
@user_namespace.param("user_id", "The user ID")
class UserById(Resource):
    @user_namespace.doc("get_user")
    @user_namespace.marshal_with(user_model)
    def get(self, user_id: int):
        if user_id not in users:
            abort(404)

        return users[user_id]


@user_namespace.route("/")
class UserResource(Resource):
    @user_namespace.doc("user_post")
    @user_namespace.expect(user_model)
    @user_namespace.marshal_with(user_out_model, code=201)
    def post(self):
        print(api.payload)
        user = api.payload
        next_id = max(users.keys()) + 1
        user["user_id"] = next_id

        users[next_id] = user
        return user


if __name__ == "__main__":
    app.run(port=8080)
```
</details>

* Good, because the way it organizes namespaces (ie. tags), and parameters is intuitive and fairly readable.
* Good, because it provides implicit [masking logic](https://flask-restx.readthedocs.io/en/latest/mask.html) that makes masking responses easy which is helpful when working with PII.
* Bad, because while you define a model, you define it as a dictionary, not a class, and thus end up working with just dictionaries. If we wanted any well-structured classes, we'd need to define that separately.
* Bad, because they have an entire section of documentation about [request parsing](https://flask-restx.readthedocs.io/en/latest/parsing.html) that is deprecated - and seems to have been replaced quite some time ago (not well maintained?).
* Bad, because the last release was over a year ago, and there have only been a very small number of commits this year.


### APIFairy

[APIFairy](https://apifairy.readthedocs.io/) is a library that runs adjacent to Flask and creates a Swagger endpoint from various models including SQLAlchemy and Marshmallow.

<details>
<summary>Example implementation</summary>

```py
from datetime import date

from apifairy import APIFairy, body, response
from flask import Flask, abort
from marshmallow import Schema, fields
from marshmallow.validate import Regexp

app = Flask(__name__)
app.config["APIFAIRY_TITLE"] = "Project Title"
app.config["APIFAIRY_VERSION"] = "1.0"
app.config["APIFAIRY_UI"] = "swagger_ui"


class BaseSchema(Schema):
    def jsonify(self, schema_obj):
        # This is probably not right at all,
        # but the docs claimed Marshmallow
        # objects should "just work", and they don't.
        out_json = {}
        for k in schema_obj._declared_fields.keys():
            out_json[k] = getattr(schema_obj, k)

        return out_json


class UserSchema(BaseSchema):
    name: str = fields.String(required=True)
    phone_number: str = fields.String(
        required=True,
        validate=Regexp("^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$"),
        metadata={"example": "123-456-7890"},
    )
    date_of_birth: date = fields.Date(required=False)


class UserOutSchema(UserSchema):
    user_id = fields.Integer()


users = {
    1: UserOutSchema.from_dict(
        {
            "user_id": 1,
            "name": "Bob Smith",
            "phone_number": "123-456-7890",
            "date_of_birth": "2000-01-01",
        }
    )
}


@app.get("/user/<int:user_id>")
@response(UserOutSchema)
def get_user(user_id: int):
    if user_id not in users:
        abort(404)

    return users[user_id]


@app.post("/user")
@body(UserSchema)
@response(UserOutSchema)
def create_user(data: dict):
    next_id = max(users.keys()) + 1

    data["user_id"] = next_id
    user = UserOutSchema.from_dict(data)
    users[next_id] = user

    return user


if __name__ == "__main__":
    apifairy = APIFairy(app)
    app.run(port=8080)

```
</details>

* Good, because the API uses Marshmallow for its data schema, which is a [well-maintained library](https://github.com/marshmallow-code/marshmallow).
* Good, because the decorators are named fairly intuitively and help make the methods clearer.
* Bad, because it insists Marshmallow "just works" but.. doesn't (see the hacky `jsonify` I had to do in the example). The very unhelpful error messages it gave about `jsonify` not existing were very frustrating.
* Bad, because the documentation doesn't have any fully working examples making it difficult to figure out a minimal viable implementation. It is written as if you're adjusting a fully-formed Marshmallow-based Flask app, and not starting from scratch.
* Bad, because there doesn't appear to be a ton of support - no questions posted anywhere, and only one article about it.

