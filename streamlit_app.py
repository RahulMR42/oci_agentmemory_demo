from __future__ import annotations

from html import escape

import streamlit as st

from app.config import get_settings
from features.agent_memory.service import (
    FRAMEWORK_SPECS,
    LANGGRAPH_FRAMEWORK,
    OPENAI_SDK_FRAMEWORK,
    REFERENCE_LINKS,
    WAYFLOW_FRAMEWORK,
    BackendLog,
    BackendStatus,
    DemoState,
    FrameworkSpec,
    build_service,
)


PAGE_LABELS = {
    "overview": "Overview",
    OPENAI_SDK_FRAMEWORK: "OpenAI SDK",
    LANGGRAPH_FRAMEWORK: "LangGraph",
    WAYFLOW_FRAMEWORK: "WayFlow",
}
PAGE_OPTIONS = [
    PAGE_LABELS["overview"],
    PAGE_LABELS[OPENAI_SDK_FRAMEWORK],
    PAGE_LABELS[LANGGRAPH_FRAMEWORK],
    PAGE_LABELS[WAYFLOW_FRAMEWORK],
]
PAGE_TO_FRAMEWORK = {
    PAGE_LABELS[OPENAI_SDK_FRAMEWORK]: OPENAI_SDK_FRAMEWORK,
    PAGE_LABELS[LANGGRAPH_FRAMEWORK]: LANGGRAPH_FRAMEWORK,
    PAGE_LABELS[WAYFLOW_FRAMEWORK]: WAYFLOW_FRAMEWORK,
}
FRAMEWORK_USER_DEFAULTS = {
    OPENAI_SDK_FRAMEWORK: "ociopenai",
    LANGGRAPH_FRAMEWORK: "ocigraph",
    WAYFLOW_FRAMEWORK: "ociwayflow",
}
# Keep the demo paths on separate memory scopes so retrieved memories,
# summaries, and context cards are easy to distinguish while presenting.
THEME_OPTIONS = ("Light", "Dark")
EXPECTED_PROGRESS_STEPS = 5
APP_TITLE = "OCI Agent Memory Console"
APP_SUBTITLE = (
    "Live comparison workspace for Oracle Agent Memory across direct OCI Responses "
    "LangGraph orchestration, and WayFlow assistant flows."
)


st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner=False)
def get_service():
    return build_service(get_settings())


def _safe_html(text: str) -> str:
    return escape(text).replace("\n", "<br>")


def _surface_html(title: str, body: str = "", *, eyebrow: str | None = None) -> str:
    eyebrow_html = f'<p class="eyebrow">{escape(eyebrow)}</p>' if eyebrow else ""
    body_html = f'<p class="body-copy">{escape(body)}</p>' if body else ""
    return f'<div class="surface">{eyebrow_html}<h3>{escape(title)}</h3>{body_html}</div>'


def _surface(title: str, body: str = "", *, eyebrow: str | None = None) -> None:
    st.markdown(_surface_html(title, body, eyebrow=eyebrow), unsafe_allow_html=True)


def _theme_tokens(theme_mode: str) -> dict[str, str]:
    if theme_mode == "Dark":
        return {
            "app_bg": "linear-gradient(180deg, #0b1120 0%, #111827 100%)",
            "sidebar_bg": "rgba(11, 17, 32, 0.98)",
            "panel": "rgba(15, 23, 42, 0.9)",
            "panel_alt": "rgba(17, 24, 39, 0.96)",
            "line": "rgba(148, 163, 184, 0.14)",
            "ink": "#e5e7eb",
            "muted": "#9ca3af",
            "accent": "#60a5fa",
            "accent_soft": "rgba(96, 165, 250, 0.14)",
            "warn": "#fca5a5",
            "warn_soft": "rgba(248, 113, 113, 0.12)",
            "metric_bg": "rgba(255, 255, 255, 0.03)",
            "chat_bg": "rgba(255, 255, 255, 0.025)",
            "shadow": "0 1px 2px rgba(0, 0, 0, 0.3), 0 16px 36px rgba(0, 0, 0, 0.18)",
            "input_bg": "rgba(255, 255, 255, 0.035)",
            "code_bg": "rgba(8, 13, 24, 0.96)",
            "success": "#34d399",
            "success_soft": "rgba(52, 211, 153, 0.12)",
        }

    return {
        "app_bg": "linear-gradient(180deg, #f4f7fb 0%, #eef2f7 100%)",
        "sidebar_bg": "rgba(247, 249, 252, 0.98)",
        "panel": "rgba(255, 255, 255, 0.94)",
        "panel_alt": "rgba(250, 252, 255, 0.98)",
        "line": "rgba(15, 23, 42, 0.08)",
        "ink": "#0f172a",
        "muted": "#64748b",
        "accent": "#2563eb",
        "accent_soft": "rgba(37, 99, 235, 0.1)",
        "warn": "#b91c1c",
        "warn_soft": "rgba(185, 28, 28, 0.1)",
        "metric_bg": "rgba(248, 250, 252, 0.92)",
        "chat_bg": "rgba(249, 250, 251, 0.92)",
        "shadow": "0 1px 2px rgba(15, 23, 42, 0.04), 0 12px 28px rgba(15, 23, 42, 0.04)",
        "input_bg": "rgba(255, 255, 255, 0.98)",
        "code_bg": "rgba(248, 250, 252, 0.98)",
        "success": "#059669",
        "success_soft": "rgba(5, 150, 105, 0.1)",
    }


def _inject_styles(theme_mode: str) -> None:
    tokens = _theme_tokens(theme_mode)
    st.markdown(
        f"""
        <style>
        :root {{
          --panel: {tokens["panel"]};
          --panel-alt: {tokens["panel_alt"]};
          --line: {tokens["line"]};
          --ink: {tokens["ink"]};
          --muted: {tokens["muted"]};
          --accent: {tokens["accent"]};
          --accent-soft: {tokens["accent_soft"]};
          --warn: {tokens["warn"]};
          --warn-soft: {tokens["warn_soft"]};
          --metric-bg: {tokens["metric_bg"]};
          --chat-bg: {tokens["chat_bg"]};
          --shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 10px 22px rgba(15, 23, 42, 0.035);
          --input-bg: {tokens["input_bg"]};
          --code-bg: {tokens["code_bg"]};
          --success: {tokens["success"]};
          --success-soft: {tokens["success_soft"]};
          --radius-lg: 18px;
          --radius-md: 14px;
          --radius-sm: 10px;
        }}

        .stApp {{
          color: var(--ink);
          font-family: "IBM Plex Sans", "Avenir Next", "Segoe UI Variable", sans-serif;
          background: {tokens["app_bg"]};
        }}

        [data-testid="stSidebar"] {{
          background: {tokens["sidebar_bg"]};
          border-right: 1px solid var(--line);
          min-width: 18rem;
          max-width: 18rem;
        }}

        [data-testid="stSidebar"] > div:first-child {{
          padding: 1rem 0.85rem;
        }}

        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"],
        button[kind="header"] {{
          display: none !important;
        }}

        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stHeader"],
        #MainMenu,
        footer {{
          display: none !important;
          visibility: hidden;
          height: 0 !important;
        }}

        [data-testid="stAppViewContainer"] > .main {{
          width: 100%;
        }}

        .main .block-container,
        .block-container,
        [data-testid="stMainBlockContainer"] {{
          max-width: none !important;
          width: 100% !important;
          margin-left: 0 !important;
          margin-right: 0 !important;
          padding: 0.7rem 1rem 2rem !important;
        }}

        [data-testid="stVerticalBlock"] {{
          gap: 0.75rem;
        }}

        h1, h2, h3 {{
          color: var(--ink);
          font-family: "IBM Plex Sans", "Avenir Next", "Segoe UI Variable", sans-serif;
          letter-spacing: 0;
          margin: 0;
          font-weight: 600;
        }}

        h1 {{
          font-size: clamp(1.7rem, 2.4vw, 2.25rem);
          line-height: 1.12;
        }}

        .title-wrap,
        .ops-bar,
        .flow-panel,
        .surface,
        .sidebar-panel,
        .login-card,
        .metric-card {{
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: var(--radius-sm);
          box-shadow: var(--shadow);
        }}

        .title-wrap,
        .ops-bar,
        .flow-panel,
        .surface,
        .sidebar-panel,
        .login-card {{
          padding: 1rem 1.15rem;
        }}

        .title-wrap {{
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 1rem;
          margin-bottom: 0.75rem;
        }}

        .title-copy {{
          min-width: 0;
        }}

        .title-copy h1 {{
          max-width: none;
        }}

        .title-meta {{
          display: flex;
          flex-wrap: wrap;
          justify-content: flex-end;
          gap: 0.45rem;
          max-width: 34rem;
        }}

        .ops-bar {{
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 0.55rem;
          background: var(--panel-alt);
          margin-bottom: 0.75rem;
        }}

        .ops-item {{
          min-width: 0;
          border-left: 2px solid var(--accent);
          padding-left: 0.65rem;
        }}

        .ops-label {{
          display: block;
          color: var(--muted);
          font-size: 0.68rem;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }}

        .ops-value {{
          color: var(--ink);
          font-weight: 600;
          overflow-wrap: anywhere;
        }}

        .metric-card {{
          padding: 0.72rem 0.8rem;
          background: var(--metric-bg);
        }}

        .sidebar-panel {{
          margin-bottom: 0.8rem;
        }}

        .eyebrow {{
          color: var(--accent);
          font-size: 0.72rem;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          margin: 0 0 0.35rem;
        }}

        .body-copy,
        .subtitle,
        .muted {{
          color: var(--muted);
          line-height: 1.55;
        }}

        .subtitle {{
          margin-top: 0.5rem;
        }}

        .chip-row {{
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-top: 0.8rem;
        }}

        .chip {{
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 0.32rem 0.62rem;
          border-radius: 999px;
          font-size: 0.7rem;
          font-weight: 600;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          border: 1px solid transparent;
        }}

        .chip.neutral {{
          background: var(--metric-bg);
          color: var(--muted);
          border-color: var(--line);
        }}

        .chip.live {{
          background: var(--accent-soft);
          color: var(--accent);
          border-color: var(--accent-soft);
        }}

        .chip.success {{
          background: var(--success-soft);
          color: var(--success);
          border-color: var(--success-soft);
        }}

        .chip.blocked {{
          background: var(--warn-soft);
          color: var(--warn);
          border-color: var(--warn-soft);
        }}

        .metric-label {{
          display: block;
          color: var(--muted);
          font-size: 0.72rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          margin-bottom: 0.28rem;
        }}

        .metric-value {{
          font-size: 0.98rem;
          font-weight: 600;
          color: var(--ink);
          word-break: break-word;
        }}

        .login-shell {{
          min-height: 72vh;
          display: flex;
          align-items: center;
          justify-content: center;
        }}

        .login-card {{
          width: min(28rem, 100%);
          padding: 1.5rem;
        }}

        .side-title {{
          font-size: 1.05rem;
          color: var(--ink);
          margin: 0;
          font-weight: 600;
        }}

        div[data-testid="stChatMessage"] {{
          background: var(--chat-bg);
          border: 1px solid var(--line);
          border-radius: var(--radius-sm);
          padding: 0.45rem 0.6rem;
        }}

        div[data-testid="stChatMessage"] + div[data-testid="stChatMessage"] {{
          margin-top: 0.6rem;
        }}

        [data-testid="stExpander"] {{
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: var(--radius-sm);
          overflow: hidden;
          box-shadow: var(--shadow);
        }}

        [data-testid="stExpander"] details summary {{
          font-weight: 600;
        }}

        [data-testid="stForm"] {{
          background: transparent;
        }}

        [data-testid="stTextInputRootElement"] input,
        [data-testid="stTextArea"] textarea {{
          background: var(--input-bg);
          color: var(--ink);
          border-radius: 10px;
        }}

        [data-testid="stCodeBlock"] pre,
        pre {{
          background: var(--code-bg);
        }}

        .stButton > button,
        .stFormSubmitButton > button {{
          border-radius: 10px;
          border: 1px solid var(--line);
          font-weight: 600;
          min-height: 2.55rem;
          box-shadow: none;
        }}

        .stButton > button {{
          background: var(--panel-alt);
          color: var(--ink);
        }}

        .stFormSubmitButton > button {{
          background: var(--accent);
          color: #ffffff;
          border-color: var(--accent);
        }}

        .response-shell,
        .detail-row,
        .framework-row,
        .diag-panel {{
          background: var(--panel-alt);
          border: 1px solid var(--line);
          border-radius: var(--radius-sm);
        }}

        .response-shell {{
          padding: 1rem;
          min-height: 7rem;
          color: var(--ink);
          line-height: 1.6;
          white-space: normal;
        }}

        .detail-row,
        .framework-row,
        .diag-panel {{
          padding: 0.9rem 1rem;
        }}

        .detail-row + .detail-row,
        .framework-row + .framework-row {{
          margin-top: 0.65rem;
        }}

        .detail-title,
        .framework-title {{
          display: block;
          color: var(--ink);
          font-weight: 600;
          margin-bottom: 0.2rem;
        }}

        .detail-meta,
        .framework-meta {{
          color: var(--muted);
          font-size: 0.82rem;
          margin-bottom: 0.32rem;
        }}

        .detail-body,
        .framework-body {{
          color: var(--muted);
          line-height: 1.55;
        }}

        .panel-note {{
          color: var(--muted);
          font-size: 0.9rem;
          margin-top: 0.5rem;
        }}

        .tiny {{
          color: var(--muted);
          font-size: 0.82rem;
        }}

        .flow-panel {{
          margin-bottom: 0.8rem;
        }}

        .flow-track {{
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 0.5rem;
          align-items: stretch;
          margin-top: 0.75rem;
        }}

        .flow-step {{
          position: relative;
          min-height: 5.6rem;
          padding: 0.72rem;
          border-radius: 8px;
          border: 1px solid var(--line);
          background: var(--metric-bg);
        }}

        .flow-step::after {{
          content: "";
          position: absolute;
          right: -0.58rem;
          top: 50%;
          width: 0.48rem;
          height: 0.48rem;
          border-top: 2px solid var(--muted);
          border-right: 2px solid var(--muted);
          transform: translateY(-50%) rotate(45deg);
          opacity: 0.65;
        }}

        .flow-step:last-child::after {{
          display: none;
        }}

        .flow-step.done {{
          border-color: var(--accent-soft);
          background: linear-gradient(180deg, var(--accent-soft), var(--metric-bg));
        }}

        .flow-step.idle {{
          opacity: 0.72;
        }}

        .flow-index {{
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 1.45rem;
          height: 1.45rem;
          border-radius: 999px;
          background: var(--panel);
          color: var(--accent);
          font-size: 0.72rem;
          font-weight: 700;
          margin-bottom: 0.48rem;
        }}

        .flow-title {{
          display: block;
          color: var(--ink);
          font-weight: 700;
          font-size: 0.9rem;
          line-height: 1.2;
        }}

        .flow-body {{
          color: var(--muted);
          font-size: 0.8rem;
          line-height: 1.35;
          margin-top: 0.35rem;
        }}

        .workspace-grid {{
          display: grid;
          grid-template-columns: minmax(0, 1.2fr) minmax(22rem, 0.8fr);
          gap: 0.9rem;
          align-items: start;
        }}

        @media (max-width: 1120px) {{
          .workspace-grid {{
            grid-template-columns: 1fr;
          }}
        }}

        [data-testid="stTabs"] {{
          margin-top: 0.8rem;
        }}

        [data-testid="stTabs"] [role="tablist"] {{
          gap: 0.35rem;
          border-bottom: 1px solid var(--line);
        }}

        [data-testid="stTabs"] [role="tab"] {{
          border-radius: 10px 10px 0 0;
          color: var(--muted);
          font-weight: 650;
        }}

        [data-testid="stTabs"] [aria-selected="true"] {{
          background: var(--panel-alt);
          color: var(--ink);
        }}

        @media (max-width: 980px) {{
          .title-wrap {{
            display: block;
          }}

          .title-meta {{
            justify-content: flex-start;
            min-width: 0;
            margin-top: 0.75rem;
          }}

          .ops-bar {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }}

          .flow-track {{
            grid-template-columns: 1fr;
          }}

          .flow-step::after {{
            right: auto;
            left: 50%;
            top: auto;
            bottom: -0.48rem;
            transform: translateX(-50%) rotate(135deg);
          }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _state_key(framework: str) -> str:
    return f"demo_state_{framework}"


def _error_key(framework: str) -> str:
    return f"turn_error_{framework}"


def _message_key(framework: str) -> str:
    return f"message_input_{framework}"


def _search_key(framework: str) -> str:
    return f"search_input_{framework}"


def _framework_user_key(framework: str) -> str:
    return f"memory_user_{framework}"


def _framework_user_id(framework: str) -> str:
    default = FRAMEWORK_USER_DEFAULTS.get(framework, "oci")
    return st.session_state.get(_framework_user_key(framework), default).strip() or default


def _ensure_state(settings, service) -> None:
    st.session_state.setdefault("theme_mode", THEME_OPTIONS[0])
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("auth_error", "")
    st.session_state.setdefault("login_username", settings.demo_username)
    st.session_state.setdefault("login_password", "")
    st.session_state.setdefault("nav_page", PAGE_LABELS["overview"])
    st.session_state.setdefault("page_selector", st.session_state.nav_page)
    st.session_state.setdefault("pending_nav_page", "")
    st.session_state.setdefault("pending_input_clear", [])

    for spec in FRAMEWORK_SPECS:
        st.session_state.setdefault(_framework_user_key(spec.slug), FRAMEWORK_USER_DEFAULTS.get(spec.slug, "oci"))
        if _state_key(spec.slug) not in st.session_state:
            st.session_state[_state_key(spec.slug)] = service.blank_state(
                framework=spec.slug,
                user_id=_framework_user_id(spec.slug),
            )
        st.session_state.setdefault(_error_key(spec.slug), "")
        st.session_state.setdefault(_message_key(spec.slug), "")
        st.session_state.setdefault(_search_key(spec.slug), "")


def _reset_framework(service, framework: str) -> None:
    st.session_state[_state_key(framework)] = service.blank_state(
        framework=framework,
        user_id=_framework_user_id(framework),
    )
    st.session_state[_error_key(framework)] = ""
    _queue_input_clear(framework)


def _reset_all_frameworks(service) -> None:
    for spec in FRAMEWORK_SPECS:
        _reset_framework(service, spec.slug)


def _blank_state_with_log(service, framework: str, *, user_id: str, log: BackendLog, note: str) -> DemoState:
    state = service.blank_state(
        framework=framework,
        user_id=user_id,
    )
    state.backend_logs = [log]
    state.progress = [note]
    state.notes = [note]
    return state


def _reset_states_for_deleted_user(service, deleted_user_id: str, log: BackendLog, note: str) -> None:
    for spec in FRAMEWORK_SPECS:
        if _framework_user_id(spec.slug) == deleted_user_id:
            st.session_state[_state_key(spec.slug)] = _blank_state_with_log(
                service,
                spec.slug,
                user_id=deleted_user_id,
                log=log,
                note=note,
            )
            st.session_state[_error_key(spec.slug)] = ""
            _queue_input_clear(spec.slug)


def _go_to_page(page_label: str) -> None:
    st.session_state.pending_nav_page = page_label
    st.rerun()


def _metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <span class="metric-label">{escape(label)}</span>
          <div class="metric-value">{escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _ops_item(label: str, value: str) -> str:
    return (
        '<div class="ops-item">'
        f'<span class="ops-label">{escape(label)}</span>'
        f'<div class="ops-value">{escape(value)}</div>'
        '</div>'
    )


def _render_title_bar(
    *,
    eyebrow: str,
    title: str,
    subtitle: str,
    chips: list[tuple[str, str]],
) -> None:
    chip_html = "".join(
        f'<span class="chip {escape(css_class)}">{escape(label)}</span>'
        for css_class, label in chips
    )
    st.markdown(
        f"""
        <div class="title-wrap">
          <div class="title-copy">
            <p class="eyebrow">{escape(eyebrow)}</p>
            <h1>{escape(title)}</h1>
            <p class="subtitle">{escape(subtitle)}</p>
          </div>
          <div class="title-meta">{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_ops_bar(items: list[tuple[str, str]]) -> None:
    st.markdown(
        f'<div class="ops-bar">{"".join(_ops_item(label, value) for label, value in items)}</div>',
        unsafe_allow_html=True,
    )


def _detail_row(title: str, body: str, *, meta: str | None = None) -> None:
    meta_html = f'<div class="detail-meta">{escape(meta)}</div>' if meta else ""
    st.markdown(
        f"""
        <div class="detail-row">
          <span class="detail-title">{escape(title)}</span>
          {meta_html}
          <div class="detail-body">{_safe_html(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _last_activity(state: DemoState) -> str:
    if not state.messages:
        return "No turns yet"
    return state.messages[-1].timestamp


def _render_live_flow(state: DemoState, spec: FrameworkSpec) -> None:
    if spec.slug == LANGGRAPH_FRAMEWORK:
        labels = [
            ("Thread", "Open or create memory thread"),
            ("Recall node", "Fetch summary, context card, memory hits"),
            ("Draft node", "Call OCI Responses"),
            ("Persist node", "Write completed turn"),
            ("Refresh", "Update chat and diagnostics"),
        ]
    elif spec.slug == WAYFLOW_FRAMEWORK:
        labels = [
            ("Thread", "Open or create memory thread"),
            ("Memory recall", "Fetch summary, context card, memory hits"),
            ("WayFlow agent", "Run Agent conversation"),
            ("Persist", "Write completed turn"),
            ("Refresh", "Update chat and diagnostics"),
        ]
    else:
        labels = [
            ("Thread", "Open or create memory thread"),
            ("Retrieval", "Fetch summary, context card, memory hits"),
            ("API call", "Call OCI Responses with OpenAI SDK"),
            ("Persist", "Write completed turn"),
            ("Refresh", "Update chat and diagnostics"),
        ]

    done_count = min(len(state.progress), len(labels))
    steps_html = []
    for index, (title, body) in enumerate(labels, start=1):
        css_class = "done" if index <= done_count else "idle"
        detail = state.progress[index - 1] if index <= len(state.progress) else body
        steps_html.append(
            (
                f'<div class="flow-step {css_class}">'
                f'<span class="flow-index">{index}</span>'
                f'<span class="flow-title">{escape(title)}</span>'
                f'<div class="flow-body">{escape(detail)}</div>'
                '</div>'
            )
        )

    st.markdown(
        (
            '<div class="flow-panel">'
            '<p class="eyebrow">Live call and retrieval path</p>'
            f'<h3>{escape(spec.label)} execution view</h3>'
            '<p class="tiny" style="margin: 0.45rem 0 0;">'
            'The pipeline updates after each live turn using the backend progress trace.'
            '</p>'
            f'<div class="flow-track">{"".join(steps_html)}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def _apply_pending_navigation() -> None:
    pending_page = st.session_state.get("pending_nav_page", "").strip()
    if pending_page and pending_page in PAGE_OPTIONS:
        st.session_state.nav_page = pending_page
        st.session_state.page_selector = pending_page
        st.session_state.pending_nav_page = ""
    elif st.session_state.get("page_selector") not in PAGE_OPTIONS:
        st.session_state.page_selector = st.session_state.nav_page


def _queue_input_clear(framework: str) -> None:
    pending_frameworks = list(st.session_state.get("pending_input_clear", []))
    if framework not in pending_frameworks:
        pending_frameworks.append(framework)
    st.session_state.pending_input_clear = pending_frameworks


def _apply_pending_input_clear() -> None:
    pending_frameworks = list(st.session_state.get("pending_input_clear", []))
    if not pending_frameworks:
        return

    for framework in pending_frameworks:
        st.session_state[_message_key(framework)] = ""
        st.session_state[_search_key(framework)] = ""
    st.session_state.pending_input_clear = []


def _render_sidebar(settings, status: BackendStatus, service) -> str:
    st.sidebar.markdown(
        f"""
        <div class="sidebar-panel">
          <p class="eyebrow">Configuration</p>
          <p class="side-title">{escape(APP_TITLE)}</p>
          <p class="tiny" style="margin: 0.45rem 0 0;">Left rail for setup, keys, and workspace control.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    main_tab, config_tab, keys_tab = st.sidebar.tabs(["Main", "Config", "Keys"])

    with main_tab:
        st.markdown("**Workspace**")
        current_page = st.radio(
            "Pages",
            PAGE_OPTIONS,
            key="page_selector",
            label_visibility="collapsed",
        )
        st.session_state.nav_page = current_page

        chip_class = "live" if status.ready else "blocked"
        st.markdown(
            f"""
            <div class="sidebar-panel">
              <p class="eyebrow">Runtime</p>
              <div class="chip {chip_class}">{escape(status.label)}</div>
              <p class="tiny" style="margin: 0.55rem 0 0;">{escape(status.reason)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_framework = PAGE_TO_FRAMEWORK.get(current_page)
        if current_framework and st.button("New thread", key="sidebar-new-thread", use_container_width=True):
            _reset_framework(service, current_framework)
            st.rerun()
        if st.button("Reset both workspaces", key="sidebar-reset-pages", use_container_width=True):
            _reset_all_frameworks(service)
            st.rerun()
        if st.button("Log out", key="sidebar-logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.login_password = ""
            st.rerun()

    with config_tab:
        st.markdown("**Display**")
        st.radio(
            "Theme",
            THEME_OPTIONS,
            key="theme_mode",
            horizontal=True,
            label_visibility="collapsed",
        )

        st.markdown("**Memory scope**")
        st.text_input(
            f"OpenAI SDK user (default: {FRAMEWORK_USER_DEFAULTS[OPENAI_SDK_FRAMEWORK]})",
            key=_framework_user_key(OPENAI_SDK_FRAMEWORK),
            help=f"Default memory user for the direct OpenAI SDK workspace: {FRAMEWORK_USER_DEFAULTS[OPENAI_SDK_FRAMEWORK]}.",
        )
        st.text_input(
            f"LangGraph user (default: {FRAMEWORK_USER_DEFAULTS[LANGGRAPH_FRAMEWORK]})",
            key=_framework_user_key(LANGGRAPH_FRAMEWORK),
            help=f"Default memory user for the OCI LangGraph workspace: {FRAMEWORK_USER_DEFAULTS[LANGGRAPH_FRAMEWORK]}.",
        )
        st.text_input(
            f"WayFlow user (default: {FRAMEWORK_USER_DEFAULTS[WAYFLOW_FRAMEWORK]})",
            key=_framework_user_key(WAYFLOW_FRAMEWORK),
            help=f"Default memory user for the WayFlow workspace: {FRAMEWORK_USER_DEFAULTS[WAYFLOW_FRAMEWORK]}.",
        )
        st.caption("Separate users make the memory scopes easy to distinguish in demos.")

        st.markdown("**Model**")
        st.code(settings.oci_genai_chat_model or "Not configured", language="text")
        st.markdown("**Region**")
        st.code(settings.oci_genai_region or "Not configured", language="text")

    with keys_tab:
        st.markdown("**Identifiers**")
        st.caption("Values are shown for validation, with secrets kept out of the UI.")
        _metric_card("Demo login", settings.demo_username)
        _metric_card("Project OCID", settings.oci_genai_project_ocid or "Missing")
        _metric_card("Compartment", settings.oci_compartment_ocid or "Missing")
        _metric_card("DB DSN", settings.agent_memory_db_dsn or "Missing")
        st.markdown("**Docs**")
        st.markdown(
            "\n".join(
                [
                    f"- [Oracle Agent Memory docs]({REFERENCE_LINKS['agent_memory_docs']})",
                    f"- [OCI Responses API]({REFERENCE_LINKS['responses_api']})",
                    f"- [LangGraph reference]({REFERENCE_LINKS['langgraph']})",
                ]
            )
        )

    return current_page


def _render_login(settings) -> None:
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="login-card">
          <p class="eyebrow">Sign in</p>
          <h1>{escape(APP_TITLE)}</h1>
          <p class="subtitle">Use the local demo login to open the live console. The default username is <strong>{escape(settings.demo_username)}</strong>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not settings.demo_password:
        st.error("APP_DEMO_PASSWORD is missing. Run `./bash.sh start` so startup can generate and print a password.")
        st.stop()

    with st.form("demo-login", clear_on_submit=False):
        st.text_input("Username", key="login_username")
        st.text_input("Password", key="login_password", type="password")
        submitted = st.form_submit_button("Enter workspace", use_container_width=True)

    if st.button("Forgot password", key="forgot-demo-password", use_container_width=True):
        print(
            f"[Agent Memory Demo] Login username: {settings.demo_username} | password: {settings.demo_password}",
            flush=True,
        )
        st.info("Password printed to the Streamlit server console.")

    if submitted:
        username = st.session_state.login_username.strip()
        password = st.session_state.login_password
        if username == settings.demo_username and password == settings.demo_password:
            st.session_state.authenticated = True
            st.session_state.auth_error = ""
            st.rerun()
        st.session_state.auth_error = "Incorrect username or password."

    if st.session_state.auth_error:
        st.error(st.session_state.auth_error)

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


def _render_blocked_state(status: BackendStatus) -> None:
    st.warning(status.reason)
    _surface(
        "Backend setup required",
        "This app only runs against real OCI and Oracle AI Database resources. It does not simulate memory behavior.",
        eyebrow="Live infrastructure",
    )
    if status.details:
        st.markdown("**Missing or failing items**")
        for item in status.details:
            st.markdown(f"- `{item}`")
    st.code("./bash.sh provision\n./bash.sh start", language="bash")


def _render_overview(settings, status: BackendStatus) -> None:
    chip_class = "live" if status.ready else "blocked"
    _render_title_bar(
        eyebrow="Overview",
        title=APP_TITLE,
        subtitle=APP_SUBTITLE,
        chips=[
            (chip_class, status.label),
            ("success", f"Theme: {st.session_state.theme_mode}"),
            ("live", f"OpenAI: {_framework_user_id(OPENAI_SDK_FRAMEWORK)}"),
            ("live", f"Graph: {_framework_user_id(LANGGRAPH_FRAMEWORK)}"),
            ("live", f"WayFlow: {_framework_user_id(WAYFLOW_FRAMEWORK)}"),
        ],
    )

    if not status.ready:
        _render_blocked_state(status)
        return

    _render_ops_bar(
        [
            ("Demo login", settings.demo_username),
            ("OCI region", settings.oci_genai_region),
            ("Responses model", settings.oci_genai_chat_model),
            ("Runtime", status.mode or "live"),
        ]
    )

    intro_col, context_col = st.columns([1.35, 0.95], gap="large")
    with intro_col:
        _surface(
            "Usage",
            "Pick a workspace from the left rail, send a real prompt, and expand the operational drawers only when you need implementation detail.",
            eyebrow="Flow",
        )
        _detail_row("1. Use separate memory users", "OpenAI SDK uses `ociopenai`, LangGraph uses `ocigraph`, and WayFlow uses `ociwayflow` by default.")
        _detail_row("2. Run the same prompt across workspaces", "Send the same task through the direct SDK path, LangGraph path, and WayFlow path.")
        _detail_row("3. Inspect only what matters", "Open Progress, Backend logs, or Memory context when you want to explain how the answer was produced.")
    with context_col:
        _surface("Session", "Current workspace settings for the live console.", eyebrow="Context")
        metric_cols = st.columns(2, gap="small")
        with metric_cols[0]:
            _metric_card("Demo login", settings.demo_username)
            _metric_card("OCI region", settings.oci_genai_region)
        with metric_cols[1]:
            _metric_card("Responses model", settings.oci_genai_chat_model)
            _metric_card("Theme", st.session_state.theme_mode)

    st.markdown("### Workspaces")
    for spec in FRAMEWORK_SPECS:
        info_col, action_col = st.columns([1.55, 0.45], gap="medium", vertical_alignment="center")
        with info_col:
            st.markdown(
                f"""
                <div class="framework-row">
                  <span class="framework-title">{escape(spec.label)}</span>
                  <div class="framework-meta">{escape(spec.eyebrow)} · {escape(spec.execution_model)}</div>
                  <div class="framework-body">{escape(spec.summary)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with action_col:
            if st.button("Open workspace", key=f"open-{spec.slug}", use_container_width=True):
                _go_to_page(PAGE_LABELS[spec.slug])


def _run_framework_turn(service, spec: FrameworkSpec) -> None:
    message_key = _message_key(spec.slug)
    search_key = _search_key(spec.slug)
    error_key = _error_key(spec.slug)
    state_key = _state_key(spec.slug)

    with st.form(f"composer-{spec.slug}", clear_on_submit=False):
        st.text_area(
            "Message",
            key=message_key,
            height=170,
            placeholder="Ask something real that should benefit from memory recall.",
        )
        with st.expander("Optional retrieval override", expanded=False):
            st.text_input(
                "Search query override",
                key=search_key,
                help="Leave blank to use the message itself as the memory recall query.",
            )
        submitted = st.form_submit_button("Send", use_container_width=True)

    if not submitted:
        return

    try:
        state = st.session_state[state_key]
        with st.spinner("Running recall, OCI Responses, and memory persistence..."):
            updated = service.process_turn(
                framework=spec.slug,
                thread_id=state.thread_id,
                user_id=_framework_user_id(spec.slug),
                agent_id=state.agent_id,
                user_message=st.session_state[message_key],
                search_query=st.session_state[search_key],
            )
        st.session_state[state_key] = updated
        st.session_state[error_key] = ""
        _queue_input_clear(spec.slug)
        st.rerun()
    except Exception as exc:
        st.session_state[error_key] = str(exc)


def _render_memory_controls(service, spec: FrameworkSpec, state: DemoState) -> None:
    state_key = _state_key(spec.slug)
    error_key = _error_key(spec.slug)
    user_id = _framework_user_id(spec.slug)

    with st.expander("🧹 Memory controls", expanded=False):
        st.caption("Delete persisted Oracle Agent Memory records for this workspace scope.")

        confirm_thread = st.checkbox(
            "Confirm current thread deletion",
            key=f"confirm_delete_thread_{spec.slug}",
            disabled=not bool(state.thread_id),
        )
        if st.button(
            "🧹 Clear current thread",
            key=f"delete_thread_{spec.slug}",
            use_container_width=True,
            disabled=not bool(state.thread_id) or not confirm_thread,
        ):
            try:
                thread_id = state.thread_id or ""
                deleted = service.delete_thread(thread_id=thread_id)
                note = f"Deleted current Agent Memory thread `{thread_id}` and cleared this workspace state."
                st.session_state[state_key] = _blank_state_with_log(
                    service,
                    spec.slug,
                    user_id=user_id,
                    log=BackendLog(
                        "OracleAgentMemory.delete_thread",
                        f"Called `delete_thread(thread_id={thread_id!r})`; deleted {deleted} thread row.",
                    ),
                    note=note,
                )
                st.session_state[error_key] = ""
                _queue_input_clear(spec.slug)
                st.rerun()
            except Exception as exc:
                st.session_state[error_key] = str(exc)

        st.divider()
        st.caption(f"Selected memory user: `{user_id}`. This deletes all memory scoped to that user.")
        confirm_user = st.checkbox(
            f"Confirm all memory deletion for `{user_id}`",
            key=f"confirm_delete_user_{spec.slug}",
        )
        typed_user = st.text_input(
            "Type the memory user to confirm",
            key=f"delete_user_typed_{spec.slug}",
            placeholder=user_id,
        )
        user_confirmed = confirm_user and typed_user.strip() == user_id
        if st.button(
            "🗑️ Delete all user memory",
            key=f"delete_user_{spec.slug}",
            use_container_width=True,
            disabled=not user_confirmed,
        ):
            try:
                deleted = service.delete_user_memory(user_id=user_id)
                note = f"Deleted all Agent Memory records scoped to user `{user_id}` and reset matching workspaces."
                _reset_states_for_deleted_user(
                    service,
                    user_id,
                    log=BackendLog(
                        "OracleAgentMemory.delete_user",
                        f"Called `delete_user(user_id={user_id!r}, cascade=True)`; deleted {deleted} user profile row.",
                    ),
                    note=note,
                )
                st.rerun()
            except Exception as exc:
                st.session_state[error_key] = str(exc)


def _render_chat_history(state: DemoState) -> None:
    if not state.messages:
        st.info("No chat yet. Send the first live turn from the composer on the right.")
        return

    for message in state.messages:
        role = "assistant" if message.role == "assistant" else "user"
        with st.chat_message(role):
            st.markdown(message.content)
            st.caption(message.timestamp)


def _render_response_window(state: DemoState) -> None:
    if not state.assistant_draft:
        st.info("The latest assistant response will appear here after the first turn.")
        return
    st.markdown(
        f'<div class="response-shell">{_safe_html(state.assistant_draft)}</div>',
        unsafe_allow_html=True,
    )


def _render_progress(state: DemoState) -> None:
    progress_ratio = 0 if not state.progress else min(len(state.progress) / EXPECTED_PROGRESS_STEPS, 1.0)
    st.progress(progress_ratio)
    if not state.progress:
        st.info("Progress will populate after the next live turn.")
        return
    for index, item in enumerate(state.progress, start=1):
        _detail_row(f"Step {index}", item)


def _render_backend_logs(logs: list[BackendLog]) -> None:
    if not logs:
        st.info("Backend logs will appear after the next live turn.")
        return
    for log in logs:
        _detail_row(log.title, log.detail)


def _render_memory_details(state: DemoState) -> None:
    if not state.search_results:
        st.info("No recall yet for this page.")
    else:
        for item in state.search_results:
            score = item.score or "n/a"
            _detail_row(item.kind, item.content, meta=f"score {score}")

    st.markdown("**Summary**")
    st.code(state.summary or "No summary yet.", language="text")
    st.markdown("**Context card**")
    st.code(state.context_card or "No context card yet.", language="xml")


def _render_sdk_calls(spec: FrameworkSpec) -> None:
    st.markdown("**Memory SDK calls**")
    st.caption("These snippets mirror the live service path in `features/agent_memory/service.py`.")

    # This diagnostics tab is intentionally a short teaching snippet instead of
    # a full file dump. It shows the exact SDK boundaries reviewers usually ask for.
    st.code(
        """def snapshot(self, *, thread: object, user_id: str, query: str) -> ThreadSnapshot:
    return ThreadSnapshot(
        thread=thread,
        summary=self.read_summary(thread),
        context_card=self.read_context_card(thread),
        memory_hits=self.search(query=query, user_id=user_id),
    )

def search(self, *, query: str, user_id: str) -> list[MemoryHit]:
    normalized_query = query.strip()
    if not normalized_query:
        return []

    results = self._memory.search(
        query=normalized_query,
        scope=self._search_scope_cls(user_id=user_id),
    )

    return [
        MemoryHit(
            kind=str(getattr(result.record, "record_type", "record")),
            content=_safe_excerpt(str(result.content), width=220),
            score=f"{float(result.score):.3f}" if result.score is not None else None,
        )
        for result in results[:6]
    ]""",
        language="python",
    )

    st.markdown("**Persistence and deletion**")
    st.code(
        """def persist_turn(self, *, thread: object, user_message: str, assistant_message: str) -> None:
    thread.add_messages(
        [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message},
        ]
    )

def delete_thread(self, thread_id: str) -> int:
    return self._memory.delete_thread(thread_id)

def delete_user_memory(self, user_id: str) -> int:
    return self._memory.delete_user(user_id, cascade=True)""",
        language="python",
    )

    if spec.slug == LANGGRAPH_FRAMEWORK:
        st.markdown("**LangGraph recall node**")
        st.code(
            """def recall_context(state: LangGraphTurnState) -> LangGraphTurnState:
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
                f"Recalled {len(snapshot.memory_hits)} memory hits.",
            )
        ],
    }""",
            language="python",
        )
        return

    if spec.slug == WAYFLOW_FRAMEWORK:
        st.markdown("**WayFlow agent path**")
        st.code(
            """snapshot = self._runtime.snapshot(
    thread=thread,
    user_id=user_id,
    query=search_query or user_message,
)
agent = self._get_wayflow_agent(agent_id=agent_id)
conversation = agent.start_conversation()
conversation.append_user_message(
    self._reply_prompt(
        frame="WayFlow Agent conversation with Agent Memory recall.",
        user_message=user_message,
        snapshot=snapshot,
    )
)
conversation.execute()
assistant_draft = conversation.get_last_message().content""",
            language="python",
        )
        return

    st.markdown("**OpenAI SDK turn path**")
    st.code(
        """thread = self._runtime.get_thread(
    thread_id=thread_id,
    user_id=user_id,
    agent_id=agent_id,
)
snapshot = self._runtime.snapshot(
    thread=thread,
    user_id=user_id,
    query=user_message,
)
assistant_draft = self._responses.generate(
    prompt=self._reply_prompt(
        frame="Direct OpenAI SDK responses.create() request.",
        user_message=user_message,
        snapshot=snapshot,
    )
)""",
        language="python",
    )


def _render_diagnostics(state: DemoState, spec: FrameworkSpec, settings) -> None:
    with st.expander("Diagnostics", expanded=False):
        logs_tab, call_tab, code_tab, api_tab, time_tab, details_tab = st.tabs(
            ["Logs", "Call", "SDK Calls", "API", "Time", "Memory"]
        )

        with logs_tab:
            _render_backend_logs(state.backend_logs)

        with call_tab:
            _render_progress(state)
            st.markdown("**Retrieval results**")
            if state.search_results:
                for item in state.search_results:
                    score = item.score or "n/a"
                    _detail_row(item.kind, item.content, meta=f"score {score}")
            else:
                st.info("No memory retrieval results yet.")

        with code_tab:
            _render_sdk_calls(spec)

        with api_tab:
            _detail_row("Framework", spec.label, meta=spec.execution_model)
            _detail_row("Responses model", settings.oci_genai_chat_model)
            _detail_row("OCI region", settings.oci_genai_region)
            _detail_row("Agent id", state.agent_id)
            _detail_row("Thread id", state.thread_id or "Pending")

        with time_tab:
            _detail_row("Last activity", _last_activity(state))
            _detail_row("Visible messages", str(len(state.messages)))
            _detail_row("Progress steps", f"{len(state.progress)} of {EXPECTED_PROGRESS_STEPS}")

        with details_tab:
            if state.notes:
                for note in state.notes:
                    _detail_row("Note", note)
            else:
                st.info("No workspace notes yet.")
            st.markdown("**Summary**")
            st.code(state.summary or "No summary yet.", language="text")
            st.markdown("**Context card**")
            st.code(state.context_card or "No context card yet.", language="xml")


def _render_framework_workspace(service, settings, status: BackendStatus, spec: FrameworkSpec) -> None:
    state: DemoState = st.session_state[_state_key(spec.slug)]
    chip_class = "live" if status.ready else "blocked"

    _render_title_bar(
        eyebrow="Workspace",
        title=f"{spec.label} Workspace",
        subtitle=spec.summary,
        chips=[
            (chip_class, status.label),
            ("live", spec.execution_model),
            ("success", _framework_user_id(spec.slug)),
        ],
    )

    if not status.ready:
        _render_blocked_state(status)
        return

    _render_ops_bar(
        [
            ("Memory user", _framework_user_id(spec.slug)),
            ("Thread", state.thread_id or "Pending"),
            ("Messages", str(len(state.messages))),
            ("Last activity", _last_activity(state)),
        ]
    )

    _render_live_flow(state, spec)

    main_left, main_right = st.columns([1.55, 0.9], gap="large")
    with main_left:
        _surface("Chat", "Conversation history for the active workspace.", eyebrow="Conversation")
        _render_chat_history(state)
    with main_right:
        _surface("Response", "Latest assistant output from the active workspace.", eyebrow="Latest output")
        _render_response_window(state)
        st.markdown("")
        _surface("New message", "Write one prompt and send it through this workspace.", eyebrow="Composer")
        if st.session_state[_error_key(spec.slug)]:
            st.error(st.session_state[_error_key(spec.slug)])
        _run_framework_turn(service, spec)
        _render_memory_controls(service, spec, state)

    _surface("Diagnostics", "Operational details stay collapsed until you need logs, SDK calls, or memory state.", eyebrow="Diagnostics")
    _render_diagnostics(state, spec, settings)


def main() -> None:
    settings = get_settings()
    service = get_service()
    _ensure_state(settings, service)
    _apply_pending_navigation()
    _apply_pending_input_clear()
    _inject_styles(st.session_state.theme_mode)
    status = service.status()

    if not st.session_state.authenticated:
        _render_login(settings)

    current_page = _render_sidebar(settings, status, service)
    if current_page == PAGE_LABELS["overview"]:
        _render_overview(settings, status)
        return

    framework = PAGE_TO_FRAMEWORK[current_page]
    spec = next(item for item in FRAMEWORK_SPECS if item.slug == framework)
    _render_framework_workspace(service, settings, status, spec)


main()
