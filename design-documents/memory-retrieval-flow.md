# Memory Retrieval Flow

## Purpose

This document explains where actual memory retrieval happens in the demo. The retrieval path is shared by both the direct OpenAI SDK workspace and the LangGraph workspace.

## Core Retrieval Call

The live retrieval call is in `features/agent_memory/service.py` inside `AgentMemoryRuntime.search()`.

```python
results = self._memory.search(
    query=normalized_query,
    scope=self._search_scope_cls(user_id=user_id),
)
```

The `query` is the user message unless the UI supplies a search override. The `scope` constrains retrieval to the selected memory user. By default, OpenAI SDK uses `ociopenai` and LangGraph uses `ocigraph`.

## Snapshot Builder

The `snapshot()` method gathers all memory context used for the model prompt.

```python
def snapshot(self, *, thread: object, user_id: str, query: str) -> ThreadSnapshot:
    return ThreadSnapshot(
        thread=thread,
        summary=self.read_summary(thread),
        context_card=self.read_context_card(thread),
        memory_hits=self.search(query=query, user_id=user_id),
    )
```

This is why the UI can display three distinct memory surfaces: summary, context card, and retrieved memory hits.

## OpenAI SDK Path

The direct SDK path calls `snapshot()` before generating the assistant answer.

```python
thread = self._runtime.get_thread(
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
        frame="Direct OpenAI SDK responses.create() request against OCI Generative AI.",
        user_message=user_message,
        snapshot=snapshot,
    )
)
```

## LangGraph Path

The LangGraph path wraps the same retrieval in a named graph node.

```python
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
    }
```

## Prompt Grounding

The assistant prompt receives the memory snapshot through `_reply_prompt()`.

```python
f"Thread summary:\n{snapshot.summary}\n\n"
f"Context card:\n{snapshot.context_card}\n\n"
f"Relevant memory:\n{_format_memory_hits(snapshot.memory_hits)}\n\n"
f"User message:\n{user_message}\n\n"
```

The model is instructed to use recalled memory only when it materially helps and not to invent prior context.

## Persistence

After the assistant response is generated, the completed turn is persisted.

```python
thread.add_messages(
    [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": assistant_message},
    ]
)
```

This makes the turn available for future summaries, context cards, and memory extraction.
