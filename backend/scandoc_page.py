from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response


# Preload before the full application's supervisor installs its filesystem guard.
ASSETS = {
    name: (Path(__file__).parent / "scandoc" / name).read_text(encoding="utf-8")
    for name in ("index.html", "app.js", "model.js", "style.css")
}
CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; "
    "connect-src 'none'; img-src 'none'; base-uri 'none'; "
    "form-action 'none'; frame-ancestors 'none'"
)
router = APIRouter()


@router.get("/scandoc", response_class=HTMLResponse)
@router.get("/scandoc/", response_class=HTMLResponse)
async def scandoc():
    return HTMLResponse(ASSETS["index.html"],
                        headers={"Content-Security-Policy": CSP})


@router.get("/scandoc/{asset}")
async def scandoc_asset(asset: str):
    media = {"app.js": "text/javascript", "model.js": "text/javascript",
             "style.css": "text/css"}
    if asset not in media:
        raise HTTPException(status_code=404, detail="Unknown sandbox asset")
    return Response(ASSETS[asset], media_type=media[asset],
                    headers={"X-Content-Type-Options": "nosniff"})


# Standalone serverless entry point does not import the native lifecycle runtime.
app = FastAPI()
app.include_router(router)


@app.get("/", include_in_schema=False)
async def preview_home():
    return RedirectResponse("/scandoc", status_code=307)
