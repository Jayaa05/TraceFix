import os
from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

db = FalkorDB(
    host=os.getenv("FALKORDB_HOST"),
    port=int(os.getenv("FALKORDB_PORT", "55296")),
    username=os.getenv("FALKORDB_USERNAME", "falkordb"),
    password=os.getenv("FALKORDB_PASSWORD"),
    ssl=False,
)

graph = db.select_graph("tracefix")


def investigate_incident(incident_id):
    print(f"\nTraceFix Investigation: {incident_id}")
    print("=" * 45)

    incident_query = """
    MATCH (i:Incident {id: $incident_id})-[:INVOLVES]->(s:Service)
    RETURN i.title AS title, s.name AS service
    """

    incident_result = graph.query(
        incident_query,
        {"incident_id": incident_id},
    )

    if not incident_result.result_set:
        print("Incident not found.")
        return

    title, failed_service = incident_result.result_set[0]

    print(f"Incident: {title}")
    print(f"Involved service: {failed_service}")

    impact_query = """
    MATCH (failed:Service {name: $service_name})
    MATCH (failed)<-[:DEPENDS_ON*1..]-(affected:Service)
    RETURN DISTINCT affected.name AS service
    """

    impact_result = graph.query(
        impact_query,
        {"service_name": failed_service},
    )

    print("\nPotentially affected services:")
    if impact_result.result_set:
        for row in impact_result.result_set:
            print(f"- {row[0]}")
    else:
        print("- None found in the current graph.")

    runbook_query = """
    MATCH (r:Runbook)-[:FOR_SERVICE]->(s:Service {name: $service_name})
    RETURN r.title AS title
    """

    runbook_result = graph.query(
        runbook_query,
        {"service_name": failed_service},
    )

    print("\nRelevant runbooks:")
    if runbook_result.result_set:
        for row in runbook_result.result_set:
            print(f"- {row[0]}")
    else:
        print("- No runbook found.")

    print("\nEvidence summary:")
    print(f"- The graph links {incident_id} to {failed_service}.")
    print("- Dependency links indicate potential impact, not proven causation.")
    print("- Confirm the failure using logs and diagnostic evidence.")


if __name__ == "__main__":
    investigate_incident("INC-001")
