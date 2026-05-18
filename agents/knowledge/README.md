# Agent knowledge base

Curated notes from real Blender MCP + Bonsai sessions. These files are for agents (and humans) working through IFC/BIM tasks without repeating investigation mistakes.

Loaded by [`knowledge_loader.py`](../knowledge_loader.py) for ADK specialists and referenced from [`.cursor/rules/blender_mcp_agent_knowledge.mdc`](../../.cursor/rules/blender_mcp_agent_knowledge.mdc).

## Index

| Topic key (`load_topic`) | File | Roles (ADK) |
|--------------------------|------|-------------|
| `index` | this README | coordinator |
| `mcp` | [mcp-blender-investigation.md](mcp-blender-investigation.md) | geometry, properties, inspector |
| `slab-sketcher` | [bonsai-slab-from-cad-sketcher.md](bonsai-slab-from-cad-sketcher.md) | geometry, properties |

## How to use

1. Read the relevant topic file **before** calling `execute_blender_code` or Bonsai operators for that workflow.
2. Start every BIM session with `bim_status` (see [workspace_config/guidelines.md](../../../workspace_config/guidelines.md)).
3. Prefer dedicated `bim_*` MCP tools; use `execute_blender_code` only for inspection or when no tool exists.
4. Update these files when a workflow is confirmed in the UI or when new MCP/API pitfalls are found.

## Slab from named sketch (summary)

- **Property:** `scene.BIMModelProperties.cad_sketch_profile_name` (lists `SlvsSketch` names).
- **Create:** `bim.add_slab_from_sketch` (Slab Tool import button).
- **Update:** `bim.edit_sketch_extrusion_profile` with sketch selected in dropdown (refresh).
- **Deploy:** Patched Bonsai in IfcOpenShell must be installed in Blender; see **Correction context** in [bonsai-slab-from-cad-sketcher.md](bonsai-slab-from-cad-sketcher.md) — **do not implement fixes until the user commands**.
- **Persist sketches:** Bonsai preference **Save non ifc data to metadata blend File** + per-project **Save session data for this file** → sidecar `*.ifc.metadata.blend` on **Save IFC Project** (see [bonsai-slab-from-cad-sketcher.md](bonsai-slab-from-cad-sketcher.md#save-cad-sketcher-sketches-with-the-ifc-metadata-file)).

## Status legend

- **MCP verified** — checked against a live Blender session via MCP.
- **Implemented in source** — code in IfcOpenShell tree; may not be loaded in Blender yet.
- **UI documented** — steps from source/manual; not yet confirmed in the viewport.
- **Gap** — known missing feature or manual step.
