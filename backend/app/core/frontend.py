from pathlib import PurePosixPath

from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class FrontendFiles(StaticFiles):
    """Serve the built SPA without turning missing API routes or assets into HTML."""

    def __init__(self, directory, api_prefix="/api"):
        super().__init__(directory=directory, html=True)
        self.api_prefix = api_prefix.strip("/")

    async def get_response(self, path, scope):
        path = path.replace("\\", "/")
        if path == self.api_prefix or path.startswith(self.api_prefix + "/"):
            raise HTTPException(status_code=404)
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or PurePosixPath(path).suffix or path.startswith("assets/"):
                raise
            return await super().get_response("index.html", scope)
