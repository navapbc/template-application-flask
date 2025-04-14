from apiflask import APIBlueprint

claimant_blueprint = APIBlueprint(
    "claimant",
    __name__,
    url_prefix="/api",
    tag="Claimant",
    description="Claimant management endpoints",
)
