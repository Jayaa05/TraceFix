# TraceFix

**An explainable, graph-powered AI incident investigation agent built with FalkorDB.**

TraceFix investigates synthetic software incidents by exploring service dependencies, finding relevant runbooks, and producing evidence-backed troubleshooting reports.

## Problem

When a software service fails, engineers must investigate dependencies, ownership, and troubleshooting documentation to understand what might be affected.

## Proposed Solution

TraceFix uses a graph database to map service relationships and an AI agent to select investigation tools, gather evidence, and explain its findings.

## Planned Technology

- Python
- FalkorDB
- Cypher
- FastAPI
- AI agent tools

## Safety and Scope

The initial version will use synthetic incident and service data. It will provide investigation guidance and safe diagnostic suggestions rather than executing destructive production actions.

## Project Status

Under development for Graph Hacks 2026.