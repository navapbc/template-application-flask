from typing import Any, Iterable

from pydantic import BaseModel


class BaseRequestModel(BaseModel):
    class Config:
        orm_mode = True

    def get_set_params(self) -> Iterable[tuple[str, Any]]:
        """
        Utility method for fetching just the parameters that were
        set when creating the pydantic model. This can be used as

        ```
        for key, value in model.get_set_params():
            ...
        ```

        and is functionally equivalent to:
        ```
        for key in model.__fields_set__:
            value = getattr(model, key)
        ```
        """
        for k in self.__fields_set__:
            yield k, getattr(self, k)
