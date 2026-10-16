
import os
from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

host = os.getenv("FALKORDB_HOST")
port = int(os.getenv("FALKORDB_PORT", "55296"))
username = os.getenv("FALKORDB_USERNAME", "falkordb")
password = os.getenv("FALKORDB_PASSWORD")

if not host or not password:
    raise ValueError("Missing FALKORDB_HOST or FALKORDB_PASSWORD in .env")

db = FalkorDB(
    host=host,
    port=port,
    username=username,
    password=password,
    ssl=False,
)

graph = db.select_graph("tracefix")
result = graph.query("MATCH (n) RETURN count(n) AS total_nodes")

print("Connection successful!")
print("Total nodes:", result.result_set[0][0])
