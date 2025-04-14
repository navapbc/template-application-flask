from apiflask import APIBlueprint

claim_blueprint = APIBlueprint(
    "claim",
    __name__,
    url_prefix="/api",
    tag="Claim",
    description="Claim management endpoints",
)
