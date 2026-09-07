---
name: houdini-pdg
description: >-
  Typed PDG/TOP graph tools for procedural task networks: create TOP
  containers and nodes, wire dependencies, apply bounded parameters, inspect
  work-item state, and cook a graph with an explicit readback contract.
license: MIT
compatibility: "dcc-mcp-houdini 0.36+, Houdini 20.5+, dcc-mcp-core 0.20.14+"
allowed-tools: Bash Read Write Edit
metadata:
  dcc-mcp:
    dcc: houdini
    layer: domain
    stage: pipeline
    version: "1.0.0"
    tags: [houdini, pdg, top, task, work-item, dependency, scheduler, pipeline]
    search-hint: "pdg top task work item dependency scheduler graph cook inspect"
    tools: tools.yaml
---

# houdini-pdg

Typed graph authoring and inspection for PDG/TOP networks. This complements
`houdini-hda-automation`: that skill focuses on HDA validation and ROP chains,
while this skill exposes graph construction, dependency wiring, and explicit
work-item readback.

## Tracer-bullet flow

1. `create_pdg_network(parent_path="/obj", network_name="topnet1")`
2. `create_pdg_node(network_path="/obj/topnet1", node_type="genericgenerator")`
3. `create_pdg_node(..., node_type="ropfetch", input_nodes=["/obj/topnet1/genericgenerator1"])`
4. `inspect_pdg_graph(node_path="/obj/topnet1")`
5. `cook_pdg_graph(node_path="/obj/topnet1", block=true)`

Node types are passed to Houdini after identifier validation. The cook response
uses `hou.TopNode.getPDGNode().workItems` for the requested task or direct TOP
children. Uninitialized PDG nodes return unavailable counts. A nonblocking cook
returns `submitted`; blocking cooks distinguish `completed`, `failed`, and
`incomplete`, including canceled or failed work items. Cooking is never retried
with different arguments after an exception. It does not infer a successful
external artifact without a downstream render or publish verification.
