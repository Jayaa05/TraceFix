
# TraceFix 🔎

**Explainable, graph-powered AI incident investigation using FalkorDB.**

TraceFix helps investigate software incidents by traversing service dependencies, identifying potentially affected services, retrieving linked runbooks, and generating evidence-backed diagnostic recommendations.

**Hackathon:** Graph Hacks 2026 — FalkorDB  
**Track:** Agents That Act on Connected Data  
**Primary graph database:** FalkorDB

## Problem

When a software service fails, engineers need to understand dependency relationships, estimate potential impact, and locate relevant troubleshooting procedures. These steps can require manually exploring multiple sources of information.

## Solution

TraceFix combines graph-based reasoning with an AI agent to investigate incidents and present explainable findings.

Instead of treating an incident as an isolated record, TraceFix follows relationships between services and connects the investigation to stored runbooks.

## Features

- **Graph-powered investigation:** Queries FalkorDB for incident and service information.
- **Dependency analysis:** Traverses service relationships to identify direct and indirect dependents.
- **Impact exploration:** Displays dependency chains and potentially affected services.
- **Runbook retrieval:** Retrieves troubleshooting guidance linked to affected services.
- **Diagnostic action plan:** Converts stored runbook guidance into recommended checks.
- **AI agent:** Uses tools to investigate incidents and explain findings.
- **Interactive dashboard:** Streamlit interface for viewing incident reports and graph evidence.
- **Evidence and uncertainty:** Distinguishes potential impact from confirmed failures and proven root causes.
- **Unknown incident handling:** Returns a clear error when an incident is not present in the graph.

Diagnostic recommendations are advisory. TraceFix does not claim that recommended checks have been executed or that a root cause has been confirmed.

## Architecture

1. **Streamlit UI** — accepts an incident ID and presents the investigation.
2. **AI agent** — selects and calls investigation tools.
3. **Python tools layer** — queries the graph, follows dependencies, and retrieves runbooks.
4. **FalkorDB** — stores incidents, services, runbooks, and their relationships.
5. **Diagnostic plan** — derives recommendations from retrieved runbook evidence.

## Graph data model

### Nodes

| Node | Purpose |
|---|---|
| `Incident` | Represents a software incident |
| `Service` | Represents a software service |
| `Runbook` | Stores troubleshooting guidance |

### Relationships

| Relationship | Direction | Meaning |
|---|---|---|
| `DEPENDS_ON` | Service → Service | A service depends on another service |
| `INVOLVES` | Incident → Service | A service is associated with an incident |
| `FOR_SERVICE` | Runbook → Service | A runbook is linked to a service |

### Example graph

```text
Incident: INC-001
       |
    INVOLVES
       v
   Database
       ^
       | DEPENDS_ON
Payment Service
       ^
       | DEPENDS_ON
  API Gateway

Runbook RB-001 ── FOR_SERVICE ──> Database
```

## Example Cypher queries

### 1. Retrieve an incident and its involved service

```cypher
MATCH (i:Incident {id: $incident_id})
      -[:INVOLVES]->(s:Service)
RETURN i.title AS title,
       s.name AS service
```

### 2. Find services that depend on a target service

```cypher
MATCH (dependent:Service)-[:DEPENDS_ON*1..10]->
      (target:Service {name: $service_name})
RETURN DISTINCT dependent.name AS service
```

### 3. Retrieve linked runbooks

```cypher
MATCH (r:Runbook)-[:FOR_SERVICE]->
      (s:Service {name: $service_name})
RETURN r.id, r.title, r.steps, r.status
```

## Technology stack

- Python
- FalkorDB
- Cypher
- Groq API for the AI agent
- Streamlit
- `python-dotenv`
- Python `unittest`

## Getting started

### Prerequisites

- Python installed
- Access to a FalkorDB instance
- A Groq API key for agent functionality

### 1. Clone the repository

```bash
git clone https://github.com/Jayaa05/TraceFix.git
cd TraceFix
```

### 2. Create and activate a virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

Install the project's dependencies using its dependency file, if provided. If no dependency file is present, install the packages required by the imports in the source code.

### 4. Configure environment variables

Create a local `.env` file containing the FalkorDB connection settings and Groq API key expected by the application.

Never commit `.env` or expose API keys in screenshots, logs, or the public repository.

### 5. Start the dashboard

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit.

### 6. Run the tests

```bash
python -m py_compile app.py tools.py agent.py
python -m unittest -v test_tools.py test_live_graph.py
```

The live graph tests require a correctly configured FalkorDB connection.

## Demo walkthrough

1. Start the Streamlit application.
2. Investigate `INC-001`.
3. Review the incident details and involved service.
4. Explore direct and indirect dependencies.
5. Inspect the linked runbook and diagnostic action plan.
6. Try an unknown incident ID to demonstrate error handling.
7. Explain how graph relationships support the investigation.

## Safety and limitations

- The project uses synthetic incident and service data.
- Dependency relationships indicate potential impact, not confirmed outages.
- Runbook recommendations are not proof of root cause.
- Diagnostic actions are not automatically executed.
- Production deployment would require appropriate authentication, authorization, observability, and operational safeguards.

## AI assistance disclosure

AI-assisted development tools were used during implementation and debugging. The source code, graph integration, tests, and application behavior should be reviewed and verified by the project author.

## Repository

https://github.com/Jayaa05/TraceFix
