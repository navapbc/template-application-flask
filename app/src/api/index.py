from fastapi import APIRouter
from fastapi.responses import HTMLResponse

# This route won't appear on the OpenAPI docs
index_router = APIRouter(include_in_schema=False)


@index_router.get("/")
def get_index() -> HTMLResponse:
    content = """
            <!Doctype html>
            <html>
                <head><title>Home</title></head>
                <body>
                    <h1>Home</h1>
                    <p>Visit <a href="/docs">/docs</a> to view the api documentation for this project.</p>
                </body>
            </html>
        """
    return HTMLResponse(content=content)
