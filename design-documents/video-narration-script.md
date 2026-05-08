# Video Narration Script

## Format

Target length: 60 to 75 seconds.

Use this script while recording the app or while showing the generated animated walkthrough GIF.

## Script

### 0:00 - 0:08: Opening

This is the OCI Agent Memory Console, a live demo workspace for showing how an enterprise assistant recalls memory, calls OCI Generative AI, and persists the completed turn.

### 0:08 - 0:18: Sidebar

The left sidebar keeps the demo setup separate from the working area. The Main tab switches between Overview, OpenAI SDK, and LangGraph. The Config tab controls theme, model, region, and the two memory users: `ociopenai` for OpenAI SDK and `ocigraph` for LangGraph.

### 0:18 - 0:30: Workspace Header

The top of each workspace shows the active execution model, runtime status, selected memory user, thread id, message count, and last activity. This makes it clear which memory scope is being used and whether the demo is starting a new thread or continuing an existing one.

### 0:30 - 0:42: Live Flow

The live call and retrieval path shows what happens during a turn. In the OpenAI SDK workspace, the app opens the thread, retrieves memory, calls OCI Responses, persists the result, and refreshes the UI. In LangGraph, the same backend flow appears as explicit graph nodes.

### 0:42 - 0:55: Conversation

The main workspace keeps conversation history on the left and the latest response plus composer on the right. A user prompt is sent through the selected framework, but both paths use the same Oracle Agent Memory backend.

### 0:55 - 1:10: Diagnostics

The bottom tabs expose implementation detail when needed. Logs show backend events, Call shows progress and memory hits, Retrieval Code shows the exact memory search path, API shows model and thread identifiers, Time shows activity metadata, and Other shows notes, summary, and context card.

### 1:10 - 1:15: Close

This structure gives a clean business demo while still making the real memory retrieval and persistence flow visible for technical reviewers.
