from src.util.env_config import PydanticBaseEnvConfig


class AppConfig(PydanticBaseEnvConfig):
    # Set HOST to 127.0.0.1 by default to avoid other machines on the network
    # from accessing the application. This is especially important if you are
    # running the application locally on a public network. This needs to be
    # overriden to 0.0.0.0 when running in a container
    host: str = "127.0.0.1"
    port: int = 8080

    # TODO - figure out how we want this configured
    use_reloader: bool = True
