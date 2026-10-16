
import os
from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()


# --------------------------------------------------
# 1. FALKORDB CONNECTION
# --------------------------------------------------

def get_graph():
    """Connect to the TraceFix graph in FalkorDB."""
    host = os.getenv("FALKORDB_HOST")
    port = int(os.getenv("FALKORDB_PORT", "55296"))
    username = os.getenv("FALKORDB_USERNAME", "falkordb")
    password = os.getenv("FALKORDB_PASSWORD")

    if not host or not password:
        raise ValueError(
            "Missing FALKORDB_HOST or FALKORDB_PASSWORD in .env"
        )

    db = FalkorDB(
        host=host,
        port=port,
        username=username,
        password=password,
        ssl=False,
    )

    return db.select_graph("tracefix")


# --------------------------------------------------
# 2. GET INCIDENT DETAILS
# --------------------------------------------------

def get_incident_details(incident_id):
    """Find an incident and its linked service."""
    graph = get_graph()

    query = """
    MATCH (i:Incident {id: $incident_id})-[:INVOLVES]->(s:Service)
    RETURN i.id, i.title, s.name
    """

    result = graph.query(query, {"incident_id": incident_id})

    if not result.result_set:
        return None

    row = result.result_set[0]

    return {
        "incident_id": row[0],
        "title": row[1],
        "service": row[2],
    }


# --------------------------------------------------
# 3. FIND POTENTIALLY AFFECTED SERVICES
# --------------------------------------------------

def find_affected_services(service_name):
    """Find services that depend directly or indirectly on a service."""
    graph = get_graph()

    query = """
    MATCH (failed:Service {name: $service_name})
    MATCH (failed)<-[:DEPENDS_ON*1..10]-(affected:Service)
    RETURN DISTINCT affected.name
    """

    result = graph.query(query, {"service_name": service_name})

    return sorted(row[0] for row in result.result_set)


# --------------------------------------------------
# 4. GET DEPENDENCY CHAINS
# --------------------------------------------------

def get_dependency_chain(service_name):
    """Return dependency paths ending at the specified service."""
    graph = get_graph()

    query = """
    MATCH path = (affected:Service)-[:DEPENDS_ON*1..10]->
                 (failed:Service {name: $service_name})
    RETURN [node IN nodes(path) | node.name]
    """

    result = graph.query(query, {"service_name": service_name})

    return [row[0] for row in result.result_set]


# --------------------------------------------------
# 5. GET LINKED RUNBOOKS
# --------------------------------------------------

def get_runbooks(service_name):
    """Retrieve runbooks linked to a service."""
    graph = get_graph()

    query = """
    MATCH (r:Runbook)-[:FOR_SERVICE]->(s:Service {name: $service_name})
    RETURN r.id, r.title, r.steps, r.status
    """

    result = graph.query(query, {"service_name": service_name})

    return [
        {
            "id": row[0],
            "title": row[1],
            "steps": row[2],
            "status": row[3],
        }
        for row in result.result_set
    ]


# --------------------------------------------------
# 6. INVESTIGATE INCIDENT
# --------------------------------------------------

def investigate_incident(incident_id):
    """Combine graph evidence into a structured incident report."""

    incident = get_incident_details(incident_id)

    if incident is None:
        return {
            "incident_id": incident_id,
            "error": "Incident not found in FalkorDB.",
        }

    service = incident["service"]

    affected_services = find_affected_services(service)
    dependency_chains = get_dependency_chain(service)
    runbooks = get_runbooks(service)

    direct_dependents = set()
    indirect_dependents = set()

    for path in dependency_chains:
        if not path or path[-1] != service or len(path) < 2:
            continue

        if len(path) == 2:
            direct_dependents.add(path[0])
        else:
            indirect_dependents.add(path[0])

    # A service reachable by both a direct and longer path is
    # classified as direct rather than indirect.
    indirect_dependents -= direct_dependents

    return {
        "incident": incident,
        "potentially_affected_services": affected_services,
        "dependency_chains": dependency_chains,
        "direct_dependents": sorted(direct_dependents),
        "indirect_dependents": sorted(indirect_dependents),
        "runbooks": runbooks,
        "evidence_note": (
            "Dependency paths indicate potential impact, not confirmed "
            "service failures or proven root cause. Validate using "
            "logs, metrics, traces, and diagnostic evidence."
        ),
    }


# --------------------------------------------------
# 7. TEST THE INVESTIGATION
# --------------------------------------------------

if __name__ == "__main__":
    from pprint import pprint

    pprint(investigate_incident("INC-001"))
