from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response


# Preload before the application's supervisor installs its filesystem guard.
ASSETS = {
    name: (Path(__file__).parent / "live_feedback" / name).read_text(encoding="utf-8")
    for name in ("index.html", "live.mjs", "model.mjs")
}
CSP = (
    "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; "
    "media-src 'self' blob:; connect-src 'none'; img-src 'none'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)
HEADERS = {
    "Content-Security-Policy": CSP,
    "Permissions-Policy": "camera=(self), microphone=(self)",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-store",
}
router = APIRouter()


@router.get("/live-feedback", response_class=HTMLResponse)
@router.get("/live-feedback/", response_class=HTMLResponse)
async def live_feedback():
    return HTMLResponse(ASSETS["index.html"], headers=HEADERS)


@router.get("/live-feedback/{asset}")
async def live_feedback_asset(asset: str):
    if asset not in ("live.mjs", "model.mjs"):
        raise HTTPException(status_code=404, detail="Unknown live-feedback asset")
    return Response(ASSETS[asset], media_type="text/javascript", headers=HEADERS)


# The preview function deliberately has no engine imports or actuation routes.
app = FastAPI()
app.include_router(router)
