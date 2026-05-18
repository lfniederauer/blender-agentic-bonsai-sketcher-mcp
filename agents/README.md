# BIM Multi-Agent (Google ADK)

Fork architecture and agent orchestration: **Luis N.** — see
[CONTRIBUTORS.md](../CONTRIBUTORS.md).

This folder contains a coordinator + specialist agent system for generic BIM workflows (Blender + Bonsai/IfcOpenShell):

- `bim_coordinator` (router/orchestrator)
- `bim_researcher` (norms and market references)
- `bim_geometry` (Blender geometry authoring/fixes)
- `bim_appearance` (materials, textures, previews)
- `bim_properties` (IFC mapping and property sets)
- `bim_costs` (quantification + cost references)
- `bim_inspector` (validation and QA)

## Architecture

The coordinator delegates to specialized agents through `AgentTool(...)`.
Specialists use filtered Blender MCP toolsets defined in `agents/tools.py`.

## Knowledge base

Session notes and workflow runbooks live in [`agents/knowledge/`](knowledge/README.md) (MCP pitfalls, Bonsai + CAD Sketcher sequences).

- **Cursor:** rules in [`.cursor/rules/`](../.cursor/rules/) (`blender_mcp_bim.mdc`, `blender_mcp_agent_knowledge.mdc`) point agents at these files.
- **ADK:** `agents/knowledge_loader.py` injects the same content into specialist instructions at startup (`geometry`, `properties`, `inspector`, coordinator index).
- **Tools:** geometry/properties agents also get `bim_execute_bonsai_op`, `bim_save_ifc`, and related `bim_*` tools for slab/sketch workflows.
- **Slab from sketch:** topic `slab-sketcher` documents `cad_sketch_profile_name`, `bim.add_slab_from_sketch`, and deploy/error correction (implement only when the user orders).

Edit markdown under `agents/knowledge/` when workflows change; ADK picks up changes on next process start (restart `bim-agent-runner` / ADK process if already running).

## Prerequisites

1. Blender running with MCP addon connected on `127.0.0.1:9876`.
2. Blender MCP HTTP service running (default `http://127.0.0.1:8050/`).
3. Environment variable `GEMINI_API_KEY` set.

## Start MCP + agent runner (Docker Compose)

From `mcp/` (starts Blender MCP HTTP and the BIM ADK agent runner):

```bash
docker compose up -d --build
docker compose ps
```

Health endpoints:

```bash
curl http://127.0.0.1:8050/health
curl http://127.0.0.1:8060/health
```

One-shot agent query over HTTP (NDJSON stream):

```bash
curl -N -X POST http://127.0.0.1:8060/api/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"bim_status and summarize the scene"}'
```

Start only the MCP service (no agent runner):

```bash
docker compose up -d --build blender-mcp
```

Start only the agent runner (MCP must already be healthy):

```bash
docker compose up -d --build bim-agent
```

## Install ADK dependencies

From repository root:

```bash
make install_agents
```

## Run one-shot coordinator query

```bash
make run_agent QUERY="bim_status, summarize the scene, and list any validation issues"
```

## Run ADK web UI

```bash
make run_agent_web
```

Then use `agents/main.py` entrypoint loaded by ADK web.

## Environment overrides

- `BLENDER_MCP_HTTP_URL` (default `http://127.0.0.1:8050/`)
- `BLENDER_MCP_HTTP_PORT` (if URL is not set, builds `http://127.0.0.1:<port>/`)
- `BIM_AGENT_HTTP_PORT` (default `8060`, Docker agent runner listen port)
- `MCP_HTTP_URL` (alias fallback)
- `GEMINI_API_KEY` (required for model calls)
- `ADK_MODEL`, `ADK_MODEL_COORDINATOR`, `ADK_MODEL_GEOMETRY`, etc.

