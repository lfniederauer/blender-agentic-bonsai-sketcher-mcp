# MCP + Blender investigation patterns

**Status:** MCP verified (2026-05-18 session, Blender 5.1, Bonsai 0.8.5, CAD Sketcher extension).

## Session checklist

1. Blender running, MCP add-on connected.
2. `bim_status` — confirm `bonsai_installed`, `ifcopenshell_installed`, `ifc_loaded`, note `ifc_path` and `active_object`.
3. Scene overview — `get_objects_summary` (optional `name_filter`; may not find sketcher-only data).
4. Targeted inspection — `execute_blender_code` with patterns below.
5. BIM mutations — `bim_*` tools or `bim_execute_bonsai_op` when appropriate.
6. Persist — `bim_save_ifc` with explicit path after edits.

## Errors we hit (and fixes)

### Wrong parameter name on `get_object_detail_summary`

**Error:** `Field required [type=missing] ... name`

**Wrong:**
```json
{ "object_name": "planta" }
```

**Right:** read the tool schema first; use `name`:
```json
{ "name": "IfcSlab/Slab" }
```

**Lesson:** Always open `/mcps/user-blender/tools/<tool>.json` before calling. CAD Sketcher sketches are **not** `bpy.data.objects`; filtering objects by `"planta"` returns nothing.

---

### Treating `scene.sketcher.entities` as a list

**Error:** `TypeError: 'SlvsEntities' object is not iterable`  
**Error:** `TypeError: object of type 'SlvsEntities' has no len()`

**Wrong:**
```python
for e in bpy.context.scene.sketcher.entities:
    ...
len(bpy.context.scene.sketcher.entities)
```

**Right:**
```python
for e in bpy.context.scene.sketcher.entities.all:
    ...
```

---

### Assuming `scene.sketcher.sketches` exists

**Error:** `AttributeError: 'SketcherProps' object has no attribute 'sketches'`

**Wrong:**
```python
for s in bpy.context.scene.sketcher.sketches:
    ...
```

**Right:** collect sketches from entities:
```python
sk = bpy.context.scene.sketcher
sketches = [
    e for e in sk.entities.all
    if type(e).__name__ == "SlvsSketch"
]
# active sketch
active = sk.active_sketch  # None if active_sketch_i == -1
```

---

### Looking for sketch names on Blender objects

**Observation:** `get_objects_summary` with `name_filter: "planta"` returned no match. Sketch **`planta`** lives in CAD Sketcher (`SlvsSketch`), not as a mesh/curve object (unless `convert_type` is MESH/BEZIER and a target object was created).

**Right:** inspect via `execute_blender_code` and `sk.entities.all`, or CAD Sketcher UI (sketch list / active sketch).

---

### Empty codebase semantic search

Searching the workspace for "Sketcher sketch slab" returned nothing useful; Bonsai integration lives in **IfcOpenShell** (`bonsai/bim/module/model/slab.py`) and **CAD Sketcher** under Blender extensions:

`~/.config/blender/5.1/extensions/user_default/CAD_Sketcher/`

**Lesson:** For Bonsai + Sketcher behavior, grep IfcOpenShell `src/bonsai` and the installed CAD Sketcher extension path, not only `blender_mcp`.

---

### Import path for CAD Sketcher in Bonsai operators

**Stock Bonsai (error-prone):**
```python
cad_sketcher = __import__("CAD_Sketcher-main")  # often fails on Blender 4.x extensions
```

**Patched Bonsai** (`IfcOpenShell/.../slab.py`, 2026-05-18): `import_cad_sketcher()` tries `bl_ext.user_default.CAD_Sketcher` first, then legacy names. Until that build is loaded in Blender, slab sketch operators report `CAD Sketcher add-on is not enabled`.

**MCP `execute_blender_code` (always prefer):**
```python
import importlib
mod = importlib.import_module("bl_ext.user_default.CAD_Sketcher.converters")
conv = mod.BezierConverter(bpy.context.scene, sketch)
conv.run()
```

Addon module name from `addon_utils.modules()` is usually `bl_ext.user_default.CAD_Sketcher`.

**Verify patched operators loaded:**
```python
hasattr(bpy.ops.bim, "add_slab_from_sketch")  # False = reload/install patched Bonsai
```

Full deploy/troubleshooting: [bonsai-slab-from-cad-sketcher.md](bonsai-slab-from-cad-sketcher.md) → *Correction context*.

## Reliable inspection snippet (CAD Sketcher)

Use this template in `execute_blender_code`:

```python
import bpy

sk = bpy.context.scene.sketcher
result = {
    "active_sketch_i": sk.active_sketch_i,
    "active_sketch": sk.active_sketch.name if sk.active_sketch else None,
    "sketches": [],
}

for e in sk.entities.all:
    if type(e).__name__ != "SlvsSketch":
        continue
    idx = e.slvs_index
    counts = {}
    lines = {"construction": 0, "profile": 0}
    for ent in sk.entities.all:
        if getattr(ent, "sketch_i", None) != idx:
            continue
        t = type(ent).__name__
        counts[t] = counts.get(t, 0) + 1
        if t == "SlvsLine2D":
            key = "construction" if ent.construction else "profile"
            lines[key] += 1
    result["sketches"].append({
        "name": e.name,
        "slvs_index": idx,
        "fill_shape": e.fill_shape,
        "convert_type": e.convert_type,
        "entities": counts,
        "lines": lines,
    })

result
```

## Tool choice

| Goal | Tool |
|------|------|
| IFC loaded? schema? | `bim_status` |
| Hierarchy / IFC tree | `bim_tree`, `bim_summary` |
| Blender object list | `get_objects_summary`, `get_object_detail_summary` (IFC objects only) |
| CAD Sketcher state | `execute_blender_code` (patterns above) |
| Run Bonsai operator | `bim_execute_bonsai_op` or `execute_blender_code` → `bpy.ops.bim.*` |
| Save IFC | `bim_save_ifc` |

Do **not** use `execute_blender_code` for routine IFC queries when a `bim_*` tool exists.

## CAD Sketcher add-on detection

```python
import addon_utils
[name for m in addon_utils.modules() if "CAD_Sketcher" in m.__name__]
# e.g. ['bl_ext.user_default.CAD_Sketcher']
```
