from api.util.env_config import PydanticBaseEnvConfig


class AppConfig(PydanticBaseEnvConfig):
    environment: str

    # Set the host to 0.0.0.0 to make the server available external
    # to the Docker container that it's running in.
    # See https://flask.palletsprojects.com/en/2.2.x/api/#flask.Flask.run
    host: str = "0.0.0.0"
    port: int = 8080
