# Blender MCPB Extension

## Description
A lightweight MCP (Model Context Protocol) server for Blender.

Allows LLM assistants to interact with a running Blender instance – inspecting scenes, executing Python code, rendering, and navigating the interface.

Workspace guidelines: [file:///home/lfn/projetos_bim/workspace_config/guidelines.md](file:///home/lfn/projetos_bim/workspace_config/guidelines.md)

## Features
It supports running arbitrary Python code within Blender. This allows for advanced scene analysis and debugging. It also contains the complete API and user manual as resources, helping the LLM to access the latest version of both documentations.

## Installation

The MCP Server can be installed via: `pip install git+https://projects.blender.org/lab/blender_mcp.git#subdirectory=mcp`. It requires an add-on in Blender for this to work.

## Running with Docker Compose (HTTP)

Container and HTTP transport in this fork: **Luis N.** ([CONTRIBUTORS.md](../CONTRIBUTORS.md)).

This package can also run as an HTTP service using FastMCP streamable HTTP, similar to a production MCP deployment.

From `mcp/`:

```bash
docker compose up --build -d
```

Service endpoints:
- MCP HTTP endpoint: `http://localhost:8050/`
- Health check: `http://localhost:8050/health`
- BIM ADK agent runner (optional `bim-agent` service): `http://localhost:8060/api/agent/chat`
- Agent health: `http://localhost:8060/health`

Set `GEMINI_API_KEY` in `mcp/.env` before starting the agent runner. See [agents/README.md](../agents/README.md).

Stop the stack:

```bash
docker compose down
```

### Add-on

The Blender TCP bridge add-on source is bundled in this directory at
`blender_mcp_addon/`. Docker only runs the MCP server; you still install the
add-on inside Blender on the host.

**From the Lab extensions repository**

* Install the Blender Lab [Extensions repository](https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html#repositories): `https://lab.blender.org/`
* Find the MCP add-on, install and enable it.

**From this repo (development)**

```bash
blender --command extension build --source-dir ./mcp/blender_mcp_addon
blender --command extension install-file mcp-1.0.0-*.zip --repo=user_default --enable
```

Enable the add-on and start the server (default `127.0.0.1:9876`) so the MCP
process can connect.

## Examples

You can find more examples in the [documentation](https://www.blender.org/lab/mcp-server/).

## BIM / IFC Integration

When the Bonsai add-on is installed, the MCP server exposes BIM tools for
IFC workflows inside Blender. Typical flow:

1. `bim_status` to verify Bonsai + IFC availability.
2. `bim_load_ifc` to open a model.
3. `bim_summary` / `bim_tree` / `bim_select` for inspection.
4. `bim_create_element` / `bim_add_pset` / `bim_assign_spatial` for authoring.
5. `bim_sync_selection` / `bim_highlight_elements` to sync Blender ↔ IFC.
6. `bim_save_ifc` to persist edits.

For advanced edits, use `bim_edit` (ifcopenshell.api) or `bim_execute_bonsai_op`
for Bonsai operators.

### Example 1: Data-block renaming: fix types

**Demo file**: [Pebble Scattering](https://www.blender.org/download/demo/geometry-nodes/fields/pebble_scattering.blend)

**User prompt**: "With the current open Blender file fix the name of all the data-blocks to remove typos. Report back which data-blocks got fixed."

**Expected behaviour:**
- `GRP-rocks` → `GRP-pebble` [optionally, this is more opiniated]
- `LGT-Lights` → `LGT-lights`
- `Compositing Nodetree` → `Compositing Node Tree`

### Example 2: Querying data relations using natural language

**Demo file**: [Pebble Scattering](https://www.blender.org/download/demo/geometry-nodes/fields/pebble_scattering.blend)

**User prompt**: "Which objects are using the following material: pebbles"

**Expected behaviour:**
7 objects:
- `GEO-pebble`
- `GEO-pebble.001`
- `GEO-pebble.002`
- `GEO-pebble.003`
- `GEO-pebble.004`
- `GEO-pebble.005`
- `GEO-pebble.006`

### Example 3: Querying data relations using natural language

**Demo file**: [Classroom](https://download.blender.org/demo/test/classroom.zip)

**User prompt**: "Analyze the scene and list the outliers: objects with highest polygon count but smaller size from the camera point of view."

**Expected behavior:**
An analysis that consider the final amount of polygons after the object modifiers are applied. This usually happens by getting the object from the dependency graph.

The biggest outliers are: `coat 1` and `alphabet`.

Depending on whether or not the RENDER context was used (as oppose to the VIEWPORT context), the biggest outlier (`coat 1`) may show 37k or 74k polygons. This is the only object that has a modifier which is only used for rendering. Every other object should report the same poly-count regardless of the context.

## Privacy Policy
See our privacy policy: https://www.blender.org/privacy-policy/

## Support
For issues: https://projects.blender.org/lab/blender_mcp/issues
