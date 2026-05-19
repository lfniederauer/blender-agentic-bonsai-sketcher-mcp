# Blender Agentic Bonsai Sketcher MCP

This repository is a BIM-focused fork of [Blender Lab's Blender MCP][Blender MCP].
It keeps the original Blender MCP bridge, then extends it into an IFC-aware
workspace for Blender, Bonsai, IfcOpenShell, CAD Sketcher workflows, and
multi-agent automation.

> Upstream Blender MCP describes itself as "a lightweight MCP (Model Context
> Protocol) server for Blender" that gives assistants a natural-language path to
> Blender's Python API, bundled documentation, and scene inspection.

That upstream work is the foundation here. This fork changes the emphasis from a
small general Blender bridge to an agentic BIM lab: inspect the scene, query or
edit IFC semantics through Bonsai/IfcOpenShell, coordinate specialist agents, and
keep repeatable runbooks for workflows that are easy to get wrong by hand.

## What This Fork Adds

- BIM and IFC MCP tools for status, loading, saving, selection, spatial trees,
  validation, clash checks, property sets, quantity extraction, Bonsai operator
  calls, and Blender/IFC object mapping.
- Streamable HTTP transport and Docker Compose services for running the MCP
  server as an HTTP endpoint instead of only stdio.
- A Google ADK BIM multi-agent runner with coordinator, geometry, appearance,
  properties, cost, research, and inspection specialists.
- Agent knowledge files under `agents/knowledge/` for Blender MCP, Bonsai, CAD
  Sketcher, and slab-from-sketch workflows.
- Workspace rules and local Cursor MCP configuration for repeatable BIM sessions.

## Architecture

The core communication path is still inherited from Blender MCP:

```text
MCP client -> blender-agentic-bonsai-sketcher-mcp server -> TCP socket -> Blender MCP add-on -> Blender
```

This fork adds an HTTP and agent layer around that path:

```text
HTTP or ADK client -> BIM agent runner -> blender-agentic-bonsai-sketcher-mcp HTTP -> Blender add-on -> Bonsai / IfcOpenShell / Blender
```

The important directories are:

- `mcp/blmcp/`: MCP server package and auto-discovered tool modules.
- `mcp/blmcp/tools/`: Blender, viewport, documentation, render, and BIM tools.
- `mcp/blmcp/tools_helpers/`: shared helpers, including Bonsai/IfcOpenShell code
  generation helpers.
- `agents/`: Google ADK coordinator and specialist agents.
- `agents/knowledge/`: curated workflow notes loaded into agents and referenced
  by Cursor rules.
- `mcp/docker-compose.yml`: local HTTP deployment for the MCP service and BIM
  agent runner.

## Quick Start

1. Install and enable the MCP add-on in Blender: https://www.blender.org/lab/mcp-server/ "blender.org/lab/mcp-server/"
2. Start the add-on TCP server in Blender (default `127.0.0.1:9876`).
3. Copy `mcp/.env.example` to `mcp/.env` and set `GEMINI_API_KEY` for agent runs.
4. From the repository root:

```bash
# MCP HTTP + BIM agent runner (background)
make agents_up

# One-shot coordinator query (starts blender-agentic-bonsai-sketcher-mcp if needed)
make run_agent QUERY="bim_status and summarize the scene"
```

Stop the stack: `make agents_down` (or `make down`). Run `make help` for all targets.

To hook up **Cursor**, **Claude Desktop**, or **ChatGPT Desktop**, see
[Connect Your MCP Client](#connect-your-mcp-client).

### Docker Compose (recommended for HTTP + agents)

From the repository root (wraps `mcp/docker-compose.yml`):

```bash
make build          # build images only
make run            # start MCP + agent runner (no rebuild)
make run-build      # build and start (same as make agents_up)
make agents_down    # stop stack
```

Or from `mcp/`:

```bash
cd mcp
cp .env.example .env   # then edit GEMINI_API_KEY
docker compose up --build -d
docker compose ps
docker compose down
```

Default service endpoints:

| Service | URL |
| --- | --- |
| MCP HTTP | `http://127.0.0.1:8050/` |
| MCP health | `http://127.0.0.1:8050/health` |
| BIM agent chat (NDJSON) | `http://127.0.0.1:8060/api/agent/chat` |
| Agent health | `http://127.0.0.1:8060/health` |

Health checks:

```bash
curl -s http://127.0.0.1:8050/health
curl -s http://127.0.0.1:8060/health
```

Start only MCP HTTP (no long-running agent API):

```bash
cd mcp && docker compose up -d --build blender-mcp
```

## Connect Your MCP Client

Use any MCP-capable assistant (Cursor, Claude Desktop, ChatGPT Desktop, etc.) to
talk to Blender through this server. Every client needs the same Blender-side
setup first:

1. Install and enable the add-on from `mcp/blender_mcp_addon/` in Blender.
2. Start the add-on TCP server in Blender (default `127.0.0.1:9876`).
3. Install the MCP package on the machine where the client runs (or use Docker
   for HTTP — see below).

Then pick how the client reaches the MCP server:

| Mode | Who starts the server | Best for |
| --- | --- | --- |
| **HTTP** | You (`make run`, Docker, or `blender-mcp --transport http`) | Docker, several clients, CI |
| **stdio** | The MCP client spawns `blender-mcp` | Claude Desktop, simple local setups |

Verify the HTTP endpoint before wiring a client:

```bash
curl -s http://127.0.0.1:8050/health
```

A copy-paste reference for this repo lives in [`.mcp.json`](.mcp.json) (HTTP +
stdio examples).

### HTTP (streamable HTTP)

Start the server, then point the client at the URL. With Docker Compose or
`make run` / `make agents_up`, the default base URL is:

`http://127.0.0.1:8050/`

On the host without Docker:

```bash
cd mcp
pip install -e .
blender-mcp --transport http --host 127.0.0.1 --port 8050
```

> The CLI default HTTP port is `8000` if you omit `--port`; this fork’s Docker
> and Compose stack use **`8050`** — keep client URLs aligned with whatever port
> you actually started.

**Cursor** — project file [`.mcp.json`](.mcp.json) at the repo root, or global /
per-project `~/.cursor/mcp.json`. Restart Cursor after edits.

```json
{
  "mcpServers": {
    "blender-agentic-bonsai-sketcher-mcp": {
      "url": "http://127.0.0.1:8050/"
    }
  }
}
```

**OpenAI ChatGPT Desktop** — config file (create if missing):

| OS | Path |
| --- | --- |
| macOS | `~/Library/Application Support/ChatGPT/chatgpt_mcp_config.json` |
| Windows | `%APPDATA%\OpenAI\ChatGPT\chatgpt_mcp_config.json` |

Use the same `mcpServers` + `url` shape as Cursor when your ChatGPT build
supports remote MCP over HTTP. If only stdio is offered, use the stdio block in
the next subsection instead.

**Claude Desktop** — prefer **stdio** (see below). Some Claude Desktop builds
do not persist MCP entries that use only a remote `url`; if the server
disappears after restart, switch to stdio or use Claude Code / Cursor with HTTP.

### stdio (client spawns `blender-mcp`)

Install the server once:

```bash
pip install -e /path/to/blender_mcp/mcp
# or: pip install git+https://projects.blender.org/lab/blender_mcp.git#subdirectory=mcp
```

Ensure `blender-mcp` is on the `PATH` seen by the desktop app (use the full path
to your venv binary if needed).

**Cursor** — [`.mcp.json`](.mcp.json) or `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "blender": {
      "type": "stdio",
      "command": "blender-mcp"
    }
  }
}
```

With a virtualenv:

```json
{
  "mcpServers": {
    "blender": {
      "type": "stdio",
      "command": "/path/to/.venv/bin/blender-mcp"
    }
  }
}
```

**Claude Desktop** — edit `claude_desktop_config.json`:

| OS | Path |
| --- | --- |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "blender": {
      "command": "blender-mcp"
    }
  }
}
```

Or with an explicit Python module:

```json
{
  "mcpServers": {
    "blender": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "blmcp"]
    }
  }
}
```

Restart Claude Desktop after saving.

**OpenAI ChatGPT Desktop** — same `command` / `args` pattern in
`chatgpt_mcp_config.json` (paths in the HTTP table above).

### Client troubleshooting

| Symptom | What to check |
| --- | --- |
| Connection refused (HTTP) | `make run` or `docker compose up` for `blender-mcp`; `curl` the `/health` URL |
| `blender-mcp`: command not found | `pip install -e mcp/`; use absolute `command` in JSON |
| Tools missing after config change | Fully quit and reopen the MCP client |
| MCP works but Blender errors | Add-on disabled or TCP server not started in Blender |
| `bim_*` failures | Bonsai/IfcOpenShell in Blender; run `bim_status` first |

More workspace conventions:
[workspace_config/guidelines.md](../workspace_config/guidelines.md).

## Agent Runner

The ADK layer is optional. It is useful when the work benefits from specialist
roles instead of one general assistant:

- `bim_coordinator`: routes work and assembles final answers.
- `bim_geometry`: Blender geometry authoring and fixes.
- `bim_appearance`: materials, viewport screenshots, and visual review.
- `bim_properties`: IFC mapping, property sets, and Bonsai semantic edits.
- `bim_costs`: quantity extraction and cost-reference support.
- `bim_inspector`: validation, QA, and clash-checking.
- `bim_researcher`: standards, references, and market information when enabled.

**Prerequisites:** Blender running with the add-on connected, `GEMINI_API_KEY` in
`mcp/.env`, and the MCP HTTP service reachable (Docker or host on port `8050`).

### One-shot CLI (Docker Compose)

`make run_agent` starts `blender-mcp` if needed, then runs a one-off `bim-agent`
container with `python -m agents.main`:

```bash
# Default query
make run_agent

# Custom query
make run_agent QUERY="bim_status, summarize the scene, and list validation issues"

# ADK coordination trace on stderr
ADK_TRACE=1 make run_agent QUERY="bim_tree for the active site"
```

### Sample queries

These work with `make run_agent QUERY="..."` or the HTTP chat API below. The
coordinator picks specialists as needed.

```bash
# Session check and scene overview
make run_agent QUERY="Run bim_status, then bim_summary and a short scene overview"

# IFC inspection
make run_agent QUERY="bim_tree from project down to storeys; list walls on the ground floor"

# Validation and QA
make run_agent QUERY="bim_validate and report the most important errors"

# Properties and authoring
make run_agent QUERY="For the selected wall, show bim_info and suggest a Pset_WallCommon update"

# Quantities
make run_agent QUERY="bim_quantify base quantities for all slabs in the model"
```

### HTTP agent API (long-running stack)

With `make agents_up` (or `docker compose up -d` in `mcp/`), chat over NDJSON:

```bash
curl -N -X POST http://127.0.0.1:8060/api/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"bim_status and summarize the scene"}'
```

Multi-turn style (last non-empty string in `messages` is used):

```bash
curl -N -X POST http://127.0.0.1:8060/api/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":["bim_status","List open validation issues from bim_validate"]}'
```

### ADK web UI (host Python)

For interactive debugging with the ADK web UI, install dependencies on the host
and run (not Docker):

```bash
make install_agents
make run_agent_web
```

Then open the ADK web UI and use `agents/main.py` as the entrypoint.

More detail: [agents/README.md](agents/README.md).

## Relationship To Upstream

This project is not a replacement for Blender Lab's work. It is a downstream fork
for BIM experimentation and automation. The Blender MCP add-on, server shape,
tool discovery pattern, bundled Blender API/manual references, and many original
scene tools come from [Blender MCP][Blender MCP].

The fork-specific work focuses on:

- IFC/Bonsai integration through MCP tools.
- Agent orchestration for BIM tasks.
- HTTP deployment and Docker packaging.
- Practical runbooks for Blender MCP, Bonsai, CAD Sketcher, and slab workflows.

When contributing changes that belong in the general Blender MCP server, prefer
small upstreamable patches. Keep BIM-specific workflows in this fork unless they
are broadly useful to Blender MCP users.

## License And Third-Party Work

The original Blender MCP source and Blender add-on files in this repository use
`GPL-3.0-or-later` SPDX headers, and this fork should be treated as
GPL-3.0-or-later unless a file states otherwise.

IfcOpenShell is used as a dependency through Bonsai/IfcOpenShell workflows. Its
library components remain under [LGPL], while Bonsai and other IfcOpenShell
applications may use GPL-3.0-or-later as documented by the IfcOpenShell project.

Credit and license boundaries matter here:

- Blender MCP and Blender documentation references belong to the Blender project
  and Blender Authors.
- IfcOpenShell and Bonsai belong to the IfcOpenShell community and their
  contributors.
- The BIM MCP tools, ADK agent runner, workspace rules, and workflow knowledge in
  this fork are fork-specific additions by **Luis N.** — see
  [CONTRIBUTORS.md](CONTRIBUTORS.md).

## Related Documentation

- [MCP package README](mcp/README.md) — add-on install, Docker, BIM tool overview
- [Agents README](agents/README.md) — ADK coordinator and specialist agents
- [Agent knowledge base](agents/knowledge/README.md)
- [Workspace guidelines](../workspace_config/guidelines.md) — BIM session rules and Cursor MCP notes

[Blender MCP]: https://projects.blender.org/lab/blender_mcp "Blender MCP"
[LGPL]: https://github.com/IfcOpenShell/IfcOpenShell/tree/master/COPYING.LESSER "LGPL-3.0-or-later"
