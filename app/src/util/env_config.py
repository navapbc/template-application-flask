import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PydanticBaseEnvConfig(BaseModel):
    """Base class for application configuration.

    Similar to Pydantic's BaseSettings class, but we implement our own method to override from the
    environment so that it can be run later, after an instance was constructed."""

    class Config:
        validate_assignment = True

    def override_from_environment(self, environ, prefix=""):
        """Recursively override field values from the given environment variable mapping."""
        for name, field in self.__fields__.items():
            if field.is_complex():
                # Nested models must be instances of this class too.
                getattr(self, name).override_from_environment(environ, prefix=name + "_")
                continue

            env_var_name = field.field_info.extra.get("env", prefix + name)
            for key in (env_var_name, env_var_name.lower(), env_var_name.upper()):
                if key in environ:
                    logging.info("override from environment", extra={"key": key})
                    setattr(self, field.name, environ[key])
                    break
