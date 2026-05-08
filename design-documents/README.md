# OCI Agent Memory Demo Design Documents

This folder contains the design and walkthrough material for the Streamlit demo.

## Documents

- [Architecture Design](architecture-design.md): end-to-end system architecture, runtime components, data flow, and operational boundaries.
- [UI Flow Design](ui-flow-design.md): user-facing workspace structure, navigation model, collapsible diagnostics, and demo flow.
- [Memory Retrieval Flow](memory-retrieval-flow.md): the exact call path used to retrieve summary, context card, and memory hits from Oracle Agent Memory.
- [Video Narration Script](video-narration-script.md): timed narration and storyboard for a walkthrough recording.

## Video Artifacts

- [Animated walkthrough GIF](video/agent-memory-ui-flow.gif): browser-playable visual walkthrough generated locally from the storyboard.
- [MP4 walkthrough](video/agent-memory-ui-flow.mp4): video version generated with `imageio` and `imageio-ffmpeg`.

The generated videos are intentionally self-contained and do not include audio. Use the narration script when recording a voice-over.
