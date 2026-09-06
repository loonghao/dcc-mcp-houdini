---
name: houdini-copernicus
description: >-
  Typed COP/Copernicus tools for image-processing networks: create a COP
  network, build a bounded filter chain, inspect connections, and validate
  cook errors before handing the result to a render or compositing workflow.
license: MIT
compatibility: "dcc-mcp-houdini 0.36+, Houdini 20.5+, dcc-mcp-core 0.20.14+"
allowed-tools: Bash Read Write Edit
metadata:
  dcc-mcp:
    dcc: houdini
    layer: domain
    stage: authoring
    version: "1.0.0"
    tags: [houdini, cop, copernicus, compositing, image, filter, raster, validation]
    search-hint: "cop copernicus image compositing raster blur colorcorrect file filter network"
    tools: tools.yaml
---

# houdini-copernicus

Typed COP network authoring and inspection. The skill uses Houdini node types
and parameter readback instead of embedding a large Python recipe, so agents
can compose the same image-processing graph with the existing node and render
skills.

## Supported filter aliases

`file`, `blur`, `composite`, `colorcorrect`, `ramp`, `null`, and `output` are
mapped to their COP node types. A raw Houdini node type may also be used when
it matches the safe identifier contract. Unsupported or unavailable node types
return a structured error.

## Tracer-bullet flow

1. `create_cop_network(parent_path="/img", network_name="copnet1")`
2. `create_cop_node(network_path="/img/copnet1", filter_type="file", parameters={...})`
3. `create_cop_node(..., filter_type="blur", input_nodes=["file1"], parameters={...})`
4. `inspect_cop_network(network_path="/img/copnet1")`
5. `validate_cop_network(network_path="/img/copnet1")`

The response exposes node paths, connection endpoints, applied/skipped
parameters, and cook errors. It does not claim a rendered image until a
downstream render skill verifies an output artifact.
