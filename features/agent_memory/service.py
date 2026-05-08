from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypedDict

from app.config import Settings


REFERENCE_LINKS = {
    "blog": "https://blogs.oracle.com/developers/oracle-ai-agent-memory-a-governed-unified-memory-core-for-enterprise-ai-agents",
    "agent_memory_docs": "https://docs.oracle.com/en/database/oracle/agent-memory/26.4/agmea/index.html",
    "agent_memory_get_started": "https://docs.oracle.com/en/database/oracle/agent-memory/26.4/agmea/get-started.html",
    "responses_api": "https://docs.oracle.com/en-us/iaas/Content/generative-ai/responses-api.htm",
    "api_keys": "https://docs.oracle.com/en-us/iaas/Content/generative-ai/api-keys.htm",
    "projects": "https://docs.oracle.com/en-us/iaas/Content/generative-ai/projects.htm",
    "langgraph": "https://reference.langchain.com/python/langgraph/",
}

OPENAI_SDK_FRAMEWORK = "openai_sdk"
LANGGRAPH_FRAMEWORK = "langgraph"
WAYFLOW_FRAMEWORK = "wayflow"


@dataclass(frozen=True)
class FrameworkSpec:
    slug: str
    label: str
    eyebrow: str
    headline: str
    summary: str
    execution_model: str
    sidebar_copy: str
    default_agent_id: str
    chips: tuple[str, ...]


FRAMEWORK_SPECS: tuple[FrameworkSpec, ...] = (
    FrameworkSpec(
        slug=OPENAI_SDK_FRAMEWORK,
        label="OpenAI SDK",
        eyebrow="Direct SDK",
        headline="Direct OCI Responses chat with Oracle Agent Memory recall.",
        summary=(
            "The cleanest live path: recall context from Oracle Agent Memory, call OCI Responses through "
            "the current OpenAI Python SDK, then persist the turn."
        ),
        execution_model="Direct `responses.create()` request",
        sidebar_copy="Fastest path for demonstrating the production request flow.",
        default_agent_id="oci_openai_sdk_assistant",
        chips=("Direct call", "OCI Responses", "Agent Memory"),
    ),
    FrameworkSpec(
        slug=LANGGRAPH_FRAMEWORK,
        label="LangGraph",
        eyebrow="State Graph",
        headline="Explicit graph orchestration on the same live backend.",
        summary=(
            "Use LangGraph to show the turn as clear steps: recall context, generate the answer, and "
            "persist the result back to Oracle Agent Memory."
        ),
        execution_model="Compiled `StateGraph` run",
        sidebar_copy="Best for demonstrating orchestration steps and graph execution.",
        default_agent_id="oci_langgraph_assistant",
        chips=("StateGraph", "Step trace", "Live infra"),
    ),
    FrameworkSpec(
        slug=WAYFLOW_FRAMEWORK,
        label="WayFlow",
        eyebrow="Agent Flow",
        headline="WayFlow assistant runtime on the same Agent Memory backend.",
        summary=(
            "Use Oracle WayFlow to demonstrate a reusable assistant flow: recall memory, run a "
            "WayFlow agent over the grounded prompt, and persist the completed turn."
        ),
        execution_model="WayFlow `Agent` conversation",
        sidebar_copy="Best for demonstrating the memory library inside Oracle's assistant runtime.",
        default_agent_id="oci_wayflow_assistant",
        chips=("WayFlow", "Agent", "Memory library"),
    ),
)

FRAMEWORK_SPEC_BY_SLUG = {item.slug: item for item in FRAMEWORK_SPECS}


@dataclass
class DisplayMessage:
    role: str
    content: str
    timestamp: str


@dataclass
class MemoryHit:
    kind: str
    content: str
    score: str | None = None


@dataclass
class BackendLog:
    title: str
    detail: str


@dataclass
class BackendStatus:
    mode: str
    label: str
    ready: bool
    reason: str
    details: list[str] = field(default_factory=list)


@dataclass
class DemoState:
    framework: str
    framework_label: str
    framework_headline: str
    execution_model: str
    thread_id: str | None
    user_id: str
    agent_id: str
    messages: list[DisplayMessage] = field(default_factory=list)
    search_results: list[MemoryHit] = field(default_factory=list)
    progress: list[str] = field(default_factory=list)
    backend_logs: list[BackendLog] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    summary: str = "No thread activity yet."
    context_card: str = "<context_card>\n  No active context yet.\n</context_card>"
    assistant_draft: str = ""


@dataclass
class ThreadSnapshot:
    thread: object
    summary: str
    context_card: str
    memory_hits: list[MemoryHit]


class LangGraphTurnState(TypedDict, total=False):
    thread: object
    user_id: str
    user_message: str
    summary: str
    context_card: str
    memory_hits: list[MemoryHit]
    assistant_reply: str
    backend_logs: list[BackendLog]


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")


def _safe_excerpt(text: str, *, width: int = 160) -> str:
    compact = " ".join(text.split())
    if len(compact) <= width:
        return compact
    return f"{compact[: width - 1].rstrip()}..."


def _framework_spec(framework: str) -> FrameworkSpec:
    return FRAMEWORK_SPEC_BY_SLUG.get(framework, FRAMEWORK_SPEC_BY_SLUG[OPENAI_SDK_FRAMEWORK])


def _oci_openai_base_url(settings: Settings) -> str:
    return f"https://inference.generativeai.{settings.oci_genai_region}.oci.oraclecloud.com/openai/v1"


def _project_headers(settings: Settings) -> dict[str, str]:
    project_id = settings.oci_genai_project_ocid.strip()
    if not project_id:
        return {}
    return {"OpenAI-Project": project_id}


def _normalize_model_name(model: str) -> str:
    normalized = model.strip()
    if normalized.startswith("oci/"):
        return normalized.split("/", 1)[1]
    return normalized


def _as_openai_provider_model(model: str) -> str:
    normalized = _normalize_model_name(model)
    if "/" in normalized:
        return normalized
    return f"openai/{normalized}"


def _native_oci_embedding_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "oci_region": settings.oci_native_region or settings.oci_genai_region,
        "oci_user": settings.oci_native_user,
        "oci_fingerprint": settings.oci_native_fingerprint,
        "oci_tenancy": settings.oci_native_tenancy,
        "oci_key_file": settings.oci_native_key_file,
        "oci_compartment_id": settings.oci_compartment_ocid,
    }


def _resolve_schema_policy(settings: Settings):
    from oracleagentmemory.core.dbschemapolicy import SchemaPolicy

    policy_map = {
        "require_existing": SchemaPolicy.REQUIRE_EXISTING,
        "create_if_empty": SchemaPolicy.CREATE_IF_EMPTY,
        "create_if_necessary": SchemaPolicy.CREATE_IF_NECESSARY,
        "recreate": SchemaPolicy.RECREATE,
    }
    policy = policy_map.get(settings.agent_memory_schema_policy)
    if policy is None:
        supported = ", ".join(policy_map.keys())
        raise ValueError(
            "Unsupported AGENT_MEMORY_SCHEMA_POLICY. "
            f"Use one of: {supported}."
        )
    return policy


def _format_memory_hits(memory_hits: list[MemoryHit]) -> str:
    if not memory_hits:
        return "- none"
    return "\n".join(f"- {item.kind}: {item.content}" for item in memory_hits[:6])


def _build_progress(existing_thread: bool, *, graph_mode: bool = False, wayflow_mode: bool = False) -> list[str]:
    if wayflow_mode:
        return [
            "Attached to existing thread." if existing_thread else "Created a new thread.",
            "Recalled summary, context card, and relevant memory.",
            "Ran the WayFlow agent conversation with the grounded memory prompt.",
            "Persisted the completed turn into Oracle Agent Memory.",
            "Refreshed the final chat, summary, context view, and WayFlow trace.",
        ]

    return [
        "Attached to existing thread." if existing_thread else "Created a new thread.",
        "Recalled summary, context card, and relevant memory.",
        "Generated the assistant answer through OCI Responses." if not graph_mode else "Ran the graph nodes to generate the answer.",
        "Persisted the completed turn into Oracle Agent Memory.",
        "Refreshed the final chat, summary, and context view.",
    ]


class OciResponsesClient:
    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI

        self._project_headers = _project_headers(settings)
        self._client = OpenAI(
            base_url=_oci_openai_base_url(settings),
            api_key=settings.oci_genai_api_key,
            project=settings.oci_genai_project_ocid,
            default_headers=self._project_headers,
        )
        self._model = settings.oci_genai_chat_model

    def generate(self, *, prompt: str) -> str:
        response = self._client.responses.create(
            model=self._model,
            input=prompt,
            extra_headers=self._project_headers,
        )
        return getattr(response, "output_text", "").strip()


class AgentMemoryRuntime:
    def __init__(self, settings: Settings) -> None:
        import oracledb
        from oracleagentmemory.apis.searchscope import SearchScope
        from oracleagentmemory.core.embedders.embedder import Embedder
        from oracleagentmemory.core.llms.llm import Llm, LlmApiType
        from oracleagentmemory.core.oracleagentmemory import OracleAgentMemory

        pool_kwargs = {
            "user": settings.agent_memory_db_user,
            "password": settings.agent_memory_db_password,
            "dsn": settings.agent_memory_db_dsn,
            "min": 1,
            "max": 4,
            "increment": 1,
        }
        if settings.agent_memory_wallet_dir:
            pool_kwargs["config_dir"] = settings.agent_memory_wallet_dir
            pool_kwargs["wallet_location"] = settings.agent_memory_wallet_dir
        if settings.agent_memory_wallet_password:
            pool_kwargs["wallet_password"] = settings.agent_memory_wallet_password

        self._pool = oracledb.create_pool(**pool_kwargs)
        self._search_scope_cls = SearchScope
        self._memory = OracleAgentMemory(
            connection=self._pool,
            embedder=Embedder(
                model=settings.agent_memory_embedding_model,
                **_native_oci_embedding_kwargs(settings),
            ),
            llm=Llm(
                model=_as_openai_provider_model(settings.oci_genai_chat_model),
                api_base=_oci_openai_base_url(settings),
                api_key=settings.oci_genai_api_key,
                api_type=LlmApiType.RESPONSES,
                project=settings.oci_genai_project_ocid,
                extra_headers=_project_headers(settings),
            ),
            extract_memories=True,
            schema_policy=_resolve_schema_policy(settings),
        )

    def get_thread(self, *, thread_id: str | None, user_id: str, agent_id: str) -> object:
        return self._memory.get_thread(thread_id) if thread_id else self._memory.create_thread(user_id=user_id, agent_id=agent_id)

    def snapshot(self, *, thread: object, user_id: str, query: str) -> ThreadSnapshot:
        return ThreadSnapshot(
            thread=thread,
            summary=self.read_summary(thread),
            context_card=self.read_context_card(thread),
            memory_hits=self.search(query=query, user_id=user_id),
        )

    def persist_turn(self, *, thread: object, user_message: str, assistant_message: str) -> None:
        thread.add_messages(
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message},
            ]
        )

    def read_summary(self, thread: object) -> str:
        try:
            summary_messages = thread.get_summary(except_last=1, token_budget=250)
            if not summary_messages:
                return "No compact summary available yet."
            first = summary_messages[0]
            return str(getattr(first, "content", "No compact summary available yet."))
        except Exception:
            return "No compact summary available yet."

    def read_context_card(self, thread: object) -> str:
        try:
            context_card = thread.get_context_card()
            if context_card:
                return str(context_card)
        except Exception:
            pass
        return "<context_card>\n  Context card not available yet.\n</context_card>"

    def search(self, *, query: str, user_id: str) -> list[MemoryHit]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        try:
            results = self._memory.search(
                query=normalized_query,
                scope=self._search_scope_cls(user_id=user_id),
            )
        except Exception:
            return []

        rendered: list[MemoryHit] = []
        for result in results[:6]:
            record = getattr(result, "record", None)
            record_type = getattr(record, "record_type", "record")
            content = getattr(result, "content", "")
            score = getattr(result, "score", None)
            rendered.append(
                MemoryHit(
                    kind=str(record_type),
                    content=_safe_excerpt(str(content), width=220),
                    score=None if score is None else f"{float(score):.3f}",
                )
            )
        return rendered

    def render_messages(self, thread: object) -> list[DisplayMessage]:
        return [
            DisplayMessage(
                role=str(getattr(item, "role", "assistant")),
                content=str(getattr(item, "content", "")),
                timestamp=str(getattr(item, "timestamp", None) or _utc_now()),
            )
            for item in thread.get_messages(start=0, end=-1)
        ][-12:]

    def build_state(
        self,
        *,
        framework: str,
        user_id: str,
        agent_id: str,
        thread: object,
        assistant_draft: str,
        progress: list[str],
        backend_logs: list[BackendLog],
        notes: list[str],
        recall_query: str,
    ) -> DemoState:
        spec = _framework_spec(framework)
        snapshot = self.snapshot(thread=thread, user_id=user_id, query=recall_query)
        return DemoState(
            framework=spec.slug,
            framework_label=spec.label,
            framework_headline=spec.headline,
            execution_model=spec.execution_model,
            thread_id=str(getattr(thread, "thread_id", None)),
            user_id=user_id,
            agent_id=agent_id,
            messages=self.render_messages(thread),
            search_results=snapshot.memory_hits,
            progress=progress,
            backend_logs=backend_logs,
            notes=notes,
            summary=snapshot.summary,
            context_card=snapshot.context_card,
            assistant_draft=assistant_draft,
        )


class AgentMemoryFeatureService:
    def status(self) -> BackendStatus:
        raise NotImplementedError

    def blank_state(
        self,
        *,
        framework: str = OPENAI_SDK_FRAMEWORK,
        user_id: str = "oci",
        agent_id: str | None = None,
    ) -> DemoState:
        spec = _framework_spec(framework)
        return DemoState(
            framework=spec.slug,
            framework_label=spec.label,
            framework_headline=spec.headline,
            execution_model=spec.execution_model,
            thread_id=None,
            user_id=user_id,
            agent_id=agent_id or spec.default_agent_id,
        )

    def process_turn(
        self,
        *,
        framework: str = OPENAI_SDK_FRAMEWORK,
        thread_id: str | None,
        user_id: str,
        agent_id: str | None,
        user_message: str,
        assistant_message: str = "",
        manual_memory: str = "",
        search_query: str = "",
    ) -> DemoState:
        raise NotImplementedError


class UnavailableOracleAgentMemoryService(AgentMemoryFeatureService):
    def __init__(self, *, reason: str, details: list[str] | None = None) -> None:
        self._reason = reason
        self._details = details or []

    def status(self) -> BackendStatus:
        return BackendStatus(
            mode="setup",
            label="Live backend unavailable",
            ready=False,
            reason=self._reason,
            details=self._details,
        )

    def process_turn(
        self,
        *,
        framework: str = OPENAI_SDK_FRAMEWORK,
        thread_id: str | None = None,
        user_id: str = "",
        agent_id: str | None = None,
        user_message: str = "",
        assistant_message: str = "",
        manual_memory: str = "",
        search_query: str = "",
    ) -> DemoState:
        del framework, thread_id, user_id, agent_id, user_message, assistant_message, manual_memory, search_query
        raise RuntimeError(self._reason)


class LiveOracleAgentMemoryService(AgentMemoryFeatureService):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._default_user_id = settings.demo_username or "oci"
        self._runtime = AgentMemoryRuntime(settings)
        self._responses = OciResponsesClient(settings)
        self._langgraph_app: object | None = None
        self._wayflow_agent: object | None = None

    def status(self) -> BackendStatus:
        return BackendStatus(
            mode="live",
            label="Oracle Agent Memory + OCI Responses",
            ready=True,
            reason="OpenAI SDK, LangGraph, and WayFlow are live against the same OCI and Oracle AI Database backend.",
        )

    def blank_state(
        self,
        *,
        framework: str = OPENAI_SDK_FRAMEWORK,
        user_id: str = "",
        agent_id: str | None = None,
    ) -> DemoState:
        return super().blank_state(
            framework=framework,
            user_id=user_id or self._default_user_id,
            agent_id=agent_id,
        )

    def process_turn(
        self,
        *,
        framework: str = OPENAI_SDK_FRAMEWORK,
        thread_id: str | None,
        user_id: str,
        agent_id: str | None,
        user_message: str,
        assistant_message: str = "",
        manual_memory: str = "",
        search_query: str = "",
    ) -> DemoState:
        del assistant_message, manual_memory
        normalized_message = user_message.strip()
        if not normalized_message:
            raise ValueError("Enter a user message before sending a turn.")

        spec = _framework_spec(framework)
        resolved_user_id = user_id.strip() or self._default_user_id
        resolved_agent_id = (agent_id or spec.default_agent_id).strip() or spec.default_agent_id

        if spec.slug == LANGGRAPH_FRAMEWORK:
            return self._run_langgraph_turn(
                thread_id=thread_id,
                user_id=resolved_user_id,
                agent_id=resolved_agent_id,
                user_message=normalized_message,
                search_query=search_query.strip(),
            )
        if spec.slug == WAYFLOW_FRAMEWORK:
            return self._run_wayflow_turn(
                thread_id=thread_id,
                user_id=resolved_user_id,
                agent_id=resolved_agent_id,
                user_message=normalized_message,
                search_query=search_query.strip(),
            )
        return self._run_openai_sdk_turn(
            thread_id=thread_id,
            user_id=resolved_user_id,
            agent_id=resolved_agent_id,
            user_message=normalized_message,
            search_query=search_query.strip(),
        )

    def _reply_prompt(self, *, frame: str, user_message: str, snapshot: ThreadSnapshot, extra_guidance: str = "") -> str:
        return (
            "You are an enterprise AI assistant grounded in Oracle Agent Memory. "
            "Answer in 3 short paragraphs or fewer. "
            "Use recalled memory only when it materially helps, and do not invent prior context.\n\n"
            f"Execution frame:\n{frame}\n\n"
            f"Thread summary:\n{snapshot.summary}\n\n"
            f"Context card:\n{snapshot.context_card}\n\n"
            f"Relevant memory:\n{_format_memory_hits(snapshot.memory_hits)}\n\n"
            f"User message:\n{user_message}\n\n"
            f"Extra guidance:\n{extra_guidance or 'Keep the reply concrete and enterprise-safe.'}"
        )

    def _run_openai_sdk_turn(
        self,
        *,
        thread_id: str | None,
        user_id: str,
        agent_id: str,
        user_message: str,
        search_query: str,
    ) -> DemoState:
        had_thread = bool(thread_id)
        thread = self._runtime.get_thread(thread_id=thread_id, user_id=user_id, agent_id=agent_id)
        snapshot = self._runtime.snapshot(thread=thread, user_id=user_id, query=user_message)
        assistant_draft = self._responses.generate(
            prompt=self._reply_prompt(
                frame="Direct OpenAI SDK `responses.create()` request against OCI Generative AI.",
                user_message=user_message,
                snapshot=snapshot,
                extra_guidance="Keep the answer concise and crisp because this page demonstrates the direct SDK path.",
            )
        )
        self._runtime.persist_turn(
            thread=thread,
            user_message=user_message,
            assistant_message=assistant_draft,
        )

        backend_logs = [
            BackendLog("Thread", "Attached to existing thread." if had_thread else "Created a new thread for this framework page."),
            BackendLog("Recall", f"Loaded summary, context card, and {len(snapshot.memory_hits)} memory hits for user `{user_id}`."),
            BackendLog("Responses API", f"Called OCI Responses through the OpenAI SDK with model `{self._settings.oci_genai_chat_model}`."),
            BackendLog("Persist", "Stored the user and assistant messages back into Oracle Agent Memory."),
        ]
        notes = [
            "This is the lowest-friction integration path in the app.",
            "Use this page when you want to explain the direct request flow without graph orchestration.",
        ]
        return self._runtime.build_state(
            framework=OPENAI_SDK_FRAMEWORK,
            user_id=user_id,
            agent_id=agent_id,
            thread=thread,
            assistant_draft=assistant_draft,
            progress=_build_progress(had_thread),
            backend_logs=backend_logs,
            notes=notes,
            recall_query=search_query or user_message,
        )

    def _get_langgraph_app(self):
        if self._langgraph_app is not None:
            return self._langgraph_app

        from langgraph.graph import START, StateGraph

        def recall_context(state: LangGraphTurnState) -> LangGraphTurnState:
            snapshot = self._runtime.snapshot(
                thread=state["thread"],
                user_id=state["user_id"],
                query=state["user_message"],
            )
            return {
                "summary": snapshot.summary,
                "context_card": snapshot.context_card,
                "memory_hits": snapshot.memory_hits,
                "backend_logs": state.get("backend_logs", []) + [
                    BackendLog(
                        "LangGraph: recall_context",
                        f"Recalled {len(snapshot.memory_hits)} memory hits and loaded live thread context for `{state['user_id']}`.",
                    )
                ],
            }

        def draft_response(state: LangGraphTurnState) -> LangGraphTurnState:
            snapshot = ThreadSnapshot(
                thread=state["thread"],
                summary=state.get("summary", "No compact summary available yet."),
                context_card=state.get("context_card", "<context_card>\n  Context card not available yet.\n</context_card>"),
                memory_hits=state.get("memory_hits", []),
            )
            assistant_reply = self._responses.generate(
                prompt=self._reply_prompt(
                    frame="LangGraph state graph orchestration with explicit recall, draft, and persist nodes.",
                    user_message=state["user_message"],
                    snapshot=snapshot,
                    extra_guidance="Make it clear, useful, and grounded in the recalled context.",
                )
            )
            return {
                "assistant_reply": assistant_reply,
                "backend_logs": state.get("backend_logs", []) + [
                    BackendLog(
                        "LangGraph: draft_response",
                        f"Generated the answer through OCI Responses with model `{self._settings.oci_genai_chat_model}`.",
                    )
                ],
            }

        def persist_turn(state: LangGraphTurnState) -> LangGraphTurnState:
            self._runtime.persist_turn(
                thread=state["thread"],
                user_message=state["user_message"],
                assistant_message=state["assistant_reply"],
            )
            return {
                "backend_logs": state.get("backend_logs", []) + [
                    BackendLog(
                        "LangGraph: persist_turn",
                        "Committed the completed turn to Oracle Agent Memory for future recalls.",
                    )
                ]
            }

        builder = StateGraph(LangGraphTurnState)
        builder.add_node("recall_context", recall_context)
        builder.add_node("draft_response", draft_response)
        builder.add_node("persist_turn", persist_turn)
        builder.add_edge(START, "recall_context")
        builder.add_edge("recall_context", "draft_response")
        builder.add_edge("draft_response", "persist_turn")
        builder.set_finish_point("persist_turn")
        self._langgraph_app = builder.compile()
        return self._langgraph_app

    def _get_wayflow_agent(self, *, agent_id: str):
        if self._wayflow_agent is not None:
            return self._wayflow_agent

        try:
            from wayflowcore.agent import Agent
            from wayflowcore.messagelist import Message
            from wayflowcore.models import (
                LlmCompletion,
                OpenAIAPIType,
                OpenAICompatibleModel,
                Prompt,
                StreamChunkType,
            )
        except ImportError as exc:
            raise RuntimeError(
                "WayFlow workspace requires `wayflowcore`. Run `pip install -e .` to install project dependencies."
            ) from exc

        project_headers = _project_headers(self._settings)
        responses_client = OciResponsesClient(self._settings)

        class OciResponsesWayFlowModel(OpenAICompatibleModel):
            def _get_headers(self) -> dict[str, object]:
                headers = super()._get_headers()
                headers.update(project_headers)
                return headers

            @staticmethod
            def _prompt_text(prompt: Prompt) -> str:
                parts: list[str] = []
                for message in prompt.messages:
                    content = message.content.strip()
                    if content:
                        parts.append(f"{message.role.upper()}:\n{content}")
                return "\n\n".join(parts)

            async def _generate_impl(self, prompt: Prompt) -> LlmCompletion:
                reply = responses_client.generate(prompt=self._prompt_text(prompt))
                message = prompt.parse_output(Message(content=reply, role="assistant"))
                return LlmCompletion(message=message, token_usage=None)

            async def _stream_generate_impl(self, prompt: Prompt):
                message = prompt.parse_output(
                    Message(
                        content=responses_client.generate(prompt=self._prompt_text(prompt)),
                        role="assistant",
                    )
                )
                yield StreamChunkType.START_CHUNK, Message(content="", role="assistant"), None
                yield StreamChunkType.TEXT_CHUNK, Message(content=message.content, role="assistant"), None
                yield StreamChunkType.END_CHUNK, message, None

        model = OciResponsesWayFlowModel(
            model_id=self._settings.oci_genai_chat_model,
            base_url=_oci_openai_base_url(self._settings),
            api_key=self._settings.oci_genai_api_key,
            api_type=OpenAIAPIType.RESPONSES,
            supports_tool_calling=False,
            name="OCI Responses via WayFlow",
            description="OpenAI-compatible OCI Responses model for the Agent Memory demo.",
        )
        self._wayflow_agent = Agent(
            llm=model,
            tools=[],
            agent_id=agent_id,
            name="OCI Agent Memory WayFlow Assistant",
            description="WayFlow agent that answers using Oracle Agent Memory recall context.",
            custom_instruction=(
                "You are an enterprise assistant running inside WayFlow. "
                "Use supplied Oracle Agent Memory context only when useful, keep answers concise, "
                "and never invent prior user history."
            ),
            # The OCI openai.gpt-oss-120b Responses deployment used by this demo does not advertise
            # tool-calling support, so keep WayFlow's default conversation tools disabled.
            can_finish_conversation=False,
            _add_talk_to_user_tool=False,
        )
        return self._wayflow_agent

    def _run_wayflow_turn(
        self,
        *,
        thread_id: str | None,
        user_id: str,
        agent_id: str,
        user_message: str,
        search_query: str,
    ) -> DemoState:
        had_thread = bool(thread_id)
        thread = self._runtime.get_thread(thread_id=thread_id, user_id=user_id, agent_id=agent_id)
        snapshot = self._runtime.snapshot(thread=thread, user_id=user_id, query=search_query or user_message)
        agent = self._get_wayflow_agent(agent_id=agent_id)
        prompt = self._reply_prompt(
            frame="WayFlow `Agent` conversation with explicit Oracle Agent Memory recall.",
            user_message=user_message,
            snapshot=snapshot,
            extra_guidance="Make it clear this response was produced through the WayFlow assistant runtime.",
        )
        conversation = agent.start_conversation()
        conversation.append_user_message(prompt)
        conversation.execute()
        assistant_message = conversation.get_last_message()
        assistant_draft = str(getattr(assistant_message, "content", "")).strip()
        if not assistant_draft:
            raise RuntimeError("WayFlow completed without returning an assistant message.")

        self._runtime.persist_turn(
            thread=thread,
            user_message=user_message,
            assistant_message=assistant_draft,
        )

        backend_logs = [
            BackendLog("Thread", "Attached to existing thread." if had_thread else "Created a new thread for this framework page."),
            BackendLog("Recall", f"Loaded summary, context card, and {len(snapshot.memory_hits)} memory hits for user `{user_id}`."),
            BackendLog("WayFlow Agent", "Started a WayFlow agent conversation over the grounded memory prompt."),
            BackendLog("Responses API", f"WayFlow called OCI Responses with model `{self._settings.oci_genai_chat_model}`."),
            BackendLog("Persist", "Stored the user and WayFlow assistant messages back into Oracle Agent Memory."),
        ]
        notes = [
            "This page demonstrates Oracle Agent Memory inside a WayFlow assistant runtime.",
            "The flow keeps memory retrieval explicit before handing the grounded prompt to WayFlow.",
        ]
        return self._runtime.build_state(
            framework=WAYFLOW_FRAMEWORK,
            user_id=user_id,
            agent_id=agent_id,
            thread=thread,
            assistant_draft=assistant_draft,
            progress=_build_progress(had_thread, wayflow_mode=True),
            backend_logs=backend_logs,
            notes=notes,
            recall_query=search_query or user_message,
        )

    def _run_langgraph_turn(
        self,
        *,
        thread_id: str | None,
        user_id: str,
        agent_id: str,
        user_message: str,
        search_query: str,
    ) -> DemoState:
        had_thread = bool(thread_id)
        thread = self._runtime.get_thread(thread_id=thread_id, user_id=user_id, agent_id=agent_id)
        graph = self._get_langgraph_app()
        result = graph.invoke(
            {
                "thread": thread,
                "user_id": user_id,
                "user_message": user_message,
                "backend_logs": [],
            }
        )
        assistant_draft = str(result.get("assistant_reply", "")).strip()
        backend_logs = list(result.get("backend_logs", []))
        notes = [
            "This page is useful when you need to explain the orchestration steps explicitly.",
            "The graph stays intentionally small so the progress and logs remain easy to follow.",
        ]
        return self._runtime.build_state(
            framework=LANGGRAPH_FRAMEWORK,
            user_id=user_id,
            agent_id=agent_id,
            thread=thread,
            assistant_draft=assistant_draft,
            progress=_build_progress(had_thread, graph_mode=True),
            backend_logs=backend_logs,
            notes=notes,
            recall_query=search_query or user_message,
        )


def build_service(settings: Settings) -> AgentMemoryFeatureService:
    if settings.agent_memory_mode == "mock":
        return UnavailableOracleAgentMemoryService(
            reason="Mock mode has been removed. This workspace only runs against provisioned OCI and Oracle AI Database resources.",
            details=[
                "Set `AGENT_MEMORY_MODE=live` or rerun `./bash.sh provision` to refresh `.env` from Terraform.",
            ],
        )

    if settings.agent_memory_mode not in {"", "auto", "live"}:
        return UnavailableOracleAgentMemoryService(
            reason="Unsupported runtime mode.",
            details=[f"Set `AGENT_MEMORY_MODE=live`. Current value: `{settings.agent_memory_mode}`."],
        )

    missing_values = [
        name
        for name, value in {
            "OCI_GENAI_PROJECT_OCID": settings.oci_genai_project_ocid,
            "OCI_GENAI_API_KEY": settings.oci_genai_api_key,
            "OCI_COMPARTMENT_OCID": settings.oci_compartment_ocid,
            "OCI_USER": settings.oci_native_user,
            "OCI_FINGERPRINT": settings.oci_native_fingerprint,
            "OCI_TENANCY": settings.oci_native_tenancy,
            "OCI_KEY_FILE": settings.oci_native_key_file,
            "AGENT_MEMORY_DB_USER": settings.agent_memory_db_user,
            "AGENT_MEMORY_DB_PASSWORD": settings.agent_memory_db_password,
            "AGENT_MEMORY_DB_DSN": settings.agent_memory_db_dsn,
            "AGENT_MEMORY_WALLET_DIR": settings.agent_memory_wallet_dir,
            "AGENT_MEMORY_WALLET_PASSWORD": settings.agent_memory_wallet_password,
            "APP_DEMO_PASSWORD": settings.demo_password,
        }.items()
        if not value
    ]
    if missing_values:
        return UnavailableOracleAgentMemoryService(
            reason="The live workspace is missing required OCI, database, or demo-login settings.",
            details=missing_values,
        )

    try:
        return LiveOracleAgentMemoryService(settings)
    except Exception as exc:
        return UnavailableOracleAgentMemoryService(
            reason="The live Oracle Agent Memory backend failed to start.",
            details=[_safe_excerpt(str(exc), width=220)],
        )
