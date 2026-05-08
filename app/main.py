from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from features.agent_memory.router import router as agent_memory_router


settings = get_settings()
templates = Jinja2Templates(directory=str(settings.repo_root))

app = FastAPI(
    title=settings.app_name,
    summary="Multi-page enterprise AI demo starter",
)
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
app.state.templates = templates
app.state.settings = settings

app.include_router(agent_memory_router)


@app.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request) -> HTMLResponse:
    feature_cards = [
        {
            "name": "OCI Agent Memory",
            "slug": "agent-memory",
            "href": request.url_for("agent_memory_demo"),
            "summary": (
                "Demonstrate governed thread memory, durable memory extraction, "
                "and OCI-backed inference for an enterprise assistant."
            ),
            "pages": ["Demo", "Architecture", "Infra"],
        }
    ]
    return templates.TemplateResponse(
        "app/templates/home.html",
        {
            "request": request,
            "page_title": "Enterprise AI Feature Studio",
            "active_nav": "home",
            "feature_cards": feature_cards,
        },
    )


@app.get("/healthz", name="healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/features", include_in_schema=False)
async def features_redirect() -> RedirectResponse:
    return RedirectResponse(url="/features/agent-memory/demo", status_code=307)
