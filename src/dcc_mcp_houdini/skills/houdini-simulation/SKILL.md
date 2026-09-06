---
name: houdini-simulation
description: >-
  Typed DOP simulation tools for Pyro, FLIP, RBD, and Vellum. Create a
  solver network, apply bounded parameters, inspect solver state, and validate
  a setup before committing to a long cook.
license: MIT
compatibility: "dcc-mcp-houdini 0.36+, Houdini 20.5+, dcc-mcp-core 0.20.14+"
allowed-tools: Bash Read Write Edit
metadata:
  dcc-mcp:
    dcc: houdini
    layer: domain
    stage: pipeline
    version: "1.0.0"
    tags: [houdini, dop, simulation, pyro, flip, rbd, vellum, solver, validation]
    search-hint: "pyro flip fluid rbd rigid vellum cloth grains dop solver simulation cache validate"
    tools: tools.yaml
---

# houdini-simulation

Typed DOP authoring and validation for the four common Houdini simulation
families. The skill deliberately separates setup from cooking: an agent can
create and inspect a solver network, read back the applied parameters, and
only then hand the node to a render or automation workflow for a long cook.

## Supported solver families

- `pyro` → `pyrosolver`
- `flip` → `flipsolver`
- `rbd` → `rbdsolver`
- `vellum` → `vellumsolver`

The node type is still resolved by Houdini at runtime. A missing solver or an
unsupported Houdini build returns a structured skill error instead of silently
creating a different simulation.

## Tracer-bullet flow

1. `create_simulation_network(parent_path="/obj", simulation_type="pyro")`
2. `configure_simulation_solver(solver_path="/obj/dopnet1/pyrosolver1", parameters={...})`
3. `inspect_simulation_network(network_path="/obj/dopnet1")`
4. `validate_simulation_setup(network_path="/obj/dopnet1", simulation_type="pyro")`
5. Pass the validated network to the existing render or automation skills for
   an explicitly requested cook.

Parameter names are validated as Houdini identifiers and applied only when a
matching parameter exists. The response includes both applied and skipped
parameters so a caller can detect a Houdini-version mismatch.
