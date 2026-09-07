# Husk procedural failure acceptance

Run the fixture in a fresh licensed Houdini process with this checkout and its
declared dependencies installed:

```sh
hython .github/scripts/run_houdini_husk_acceptance.py
```

The fixture exports a small USD skin and guides with deliberately missing hair
attributes, then launches a real durable Husk job through the skill entrypoints.
It asserts that a zero-exit render with a nonempty EXR and `hou.OperationFailed`
returns `state=failed` and `render_outcome=completed_with_render_errors`, while
preserving verified written-file evidence. A 120-second polling deadline cancels
an unfinished job. Temporary scene/output files and job records remain available
for inspection; no existing UI scene is used.

The final marker is `HOUDINI_HUSK_ACCEPTANCE_PASSED`. This tests the renderer and
job contract directly, rather than MCP transport or final image quality.
The complete-log regression (errors outside the final 64 KB, split severity
tokens, bounded diagnostic storage, and unreadable logs) is covered separately
by `tests/test_husk_render.py`.
