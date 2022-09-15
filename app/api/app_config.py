from api.util.env_config import PydanticBaseEnvConfig


class AppConfig(PydanticBaseEnvConfig):
    environment: str
