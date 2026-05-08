from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import get_settings
from features.agent_memory.service import AgentMemoryFeatureService, build_service


router = APIRouter(prefix="/features/agent-memory", tags=["agent-memory"])


@lru_cache(maxsize=1)
def get_service() -> AgentMemoryFeatureService:
    return build_service(get_settings())


def _feature_context(request: Request, *, active_nav: str) -> dict[str, object]:
    service = get_service()
    return {
        "request": request,
        "active_nav": active_nav,
        "feature_name": "OCI Agent Memory",
        "service_status": service.status(),
    }


@router.get("/", include_in_schema=False)
async def feature_root() -> RedirectResponse:
    return RedirectResponse(url="/features/agent-memory/demo", status_code=307)


@router.get("/demo", response_class=HTMLResponse, name="agent_memory_demo")
async def demo_page(request: Request) -> HTMLResponse:
    service = get_service()
    state = service.blank_state()
    return request.app.state.templates.TemplateResponse(
        "features/agent_memory/templates/agent_memory/demo.html",
        {
            **_feature_context(request, active_nav="demo"),
            "page_title": "Agent Memory Demo",
            "demo_state": state,
        },
    )


@router.post("/demo", response_class=HTMLResponse, name="agent_memory_demo_post")
async def demo_submit(
    request: Request,
    action: str = Form("submit"),
    thread_id: str = Form(""),
    user_id: str = Form("demo_user_001"),
    agent_id: str = Form("enterprise_assistant"),
    user_message: str = Form(""),
    assistant_message: str = Form(""),
    manual_memory: str = Form(""),
    search_query: str = Form(""),
) -> HTMLResponse:
    service = get_service()

    if action == "reset":
        state = service.blank_state(user_id=user_id, agent_id=agent_id)
    else:
        state = service.process_turn(
            thread_id=thread_id.strip() or None,
            user_id=user_id.strip() or "demo_user_001",
            agent_id=agent_id.strip() or "enterprise_assistant",
            user_message=user_message.strip(),
            assistant_message=assistant_message.strip(),
            manual_memory=manual_memory.strip(),
            search_query=search_query.strip(),
        )

    return request.app.state.templates.TemplateResponse(
        "features/agent_memory/templates/agent_memory/demo.html",
        {
            **_feature_context(request, active_nav="demo"),
            "page_title": "Agent Memory Demo",
            "demo_state": state,
        },
    )


@router.get("/architecture", response_class=HTMLResponse, name="agent_memory_architecture")
async def architecture_page(request: Request) -> HTMLResponse:
    architecture_steps = [
        "FastAPI handles the multi-page UI and feature routing.",
        "OCI Responses API can generate assistant replies by using an OCI Generative AI project and API key.",
        "The `oracleagentmemory` Python SDK persists thread state and durable memories in Oracle AI Database.",
        "The Streamlit entrypoint now compares direct OpenAI SDK and LangGraph orchestration paths on the same live backend.",
    ]
    return request.app.state.templates.TemplateResponse(
        "features/agent_memory/templates/agent_memory/architecture.html",
        {
            **_feature_context(request, active_nav="architecture"),
            "page_title": "Agent Memory Architecture",
            "architecture_steps": architecture_steps,
        },
    )


@router.get("/infra", response_class=HTMLResponse, name="agent_memory_infra")
async def infra_page(request: Request) -> HTMLResponse:
    terraform_items = [
        "Creates an OCI Generative AI project by wrapping the OCI CLI in Terraform-managed steps.",
        "Creates an OCI Generative AI API key and stores the raw one-time response in a local generated folder.",
        "Optionally creates the IAM policy required for API-key based Responses API calls.",
        "Keeps the feature-specific infrastructure isolated under `features/agent_memory/infra/terraform`.",
    ]
    required_values = [
        "OCI region",
        "Compartment OCID",
        "OCI CLI profile or auth mode",
        "Oracle AI Database connection values for `oracleagentmemory`",
        "Optional IAM group name for the API key runtime policy",
    ]
    return request.app.state.templates.TemplateResponse(
        "features/agent_memory/templates/agent_memory/infra.html",
        {
            **_feature_context(request, active_nav="infra"),
            "page_title": "Agent Memory Infra",
            "terraform_items": terraform_items,
            "required_values": required_values,
        },
    )
