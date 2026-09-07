# Typed modeling acceptance

In a fresh licensed Houdini Python process, with this checkout installed:

```sh
hython .github/scripts/run_houdini_modeling_acceptance.py
```

The runner uses MCP calls while `serve_headless` pumps HOM on its owner thread.
It creates a uniquely named transient object, authors three fuselage sections,
lofts them, bevels a rim blockout, builds a four-blade radial array, verifies
geometry and orientation receipts, and deletes the object. A failure is rethrown
on the owner thread and exits nonzero.

The final marker records typed-call and raw-scripting counts for this focused
fixture. It excludes loading and cleanup from the denominator. This is not a
replay or visual acceptance of the full Apache reference asset, materials, UVs,
hierarchy, and renders.

On Houdini 22.0.368 / Core 0.20.14, the fixture completed with 13 typed authoring
calls, zero raw scripting calls, 16 loft primitives, 56 beveled points, and
32 rotor points. The complete issue #266 reference evaluation remains separate.
