# ADR 0002: Add dedicated simulation, COP, and PDG skill boundaries

## Status

Accepted

## Context

The adapter already exposes generic node, render, HDA, and scene tools, but the
most common Houdini domain families in the capability matrix were still only
reachable through generic scripting or a broad HDA automation tool. That makes
solver selection, COP graph composition, and PDG dependency readback difficult
to discover and hard to validate before a long-running operation.

## Decision

Add three independently loadable skill packages:

- `houdini-simulation` owns typed DOP setup and validation for Pyro, FLIP, RBD,
  and Vellum.
- `houdini-copernicus` owns COP network and filter graph authoring plus
  connection/cook validation.
- `houdini-pdg` owns TOP graph construction, dependency wiring, work-item
  inspection, and explicit graph cooking.

Each package uses typed tool schemas, bounded Houdini parameter identifiers,
structured readback, and no implicit long cook. Simulation and PDG cooking stay
separate from setup and inspection so callers can choose the existing durable
job/render workflows when a real scene requires them.

## Consequences

The bundled catalog grows by three skills and thirteen typed tools. Minimal mode
does not load them; they are available through the existing progressive stage
loader. Mock-hou tests can exercise the contracts without a licensed Houdini
installation, while live acceptance still requires a real Houdini host.
