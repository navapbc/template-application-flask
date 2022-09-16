from pydantic import BaseModel


class BaseRequestModel(BaseModel):
    class Config:
        orm_mode = True
