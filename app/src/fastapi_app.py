import fastapi
import logging
import logger as our_logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

def create_app() -> fastapi.FastAPI:
    our_logging.init(__package__)

    logger.info("Creating app")
    return fastapi.FastAPI()

app = create_app()

@app.get("/")
def root():
    logger.info("hello - in the root")
    return {"message": "hello"}

class NestedA(BaseModel):
    x: str = Field(examples=["hello there again"])


class NestedB(BaseModel):
    y: list[NestedA]

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    z: list[NestedB]

@app.post("/items/")
def create_item(item: Item) -> Item:
    logger.info(item)
    return item