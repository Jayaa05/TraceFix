
import os
import json

from dotenv import load_dotenv
from groq import Groq

from tools import (
    get_incident_details,
    find_affected_services,
    get_runbooks,
    get_dependency_chain,
    investigate_incident,
)

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("Missing GROQ_API_KEY in .env")

client = Groq(api_key=api_key)

MODEL = "openai/gpt-oss-120b"


# --------------------------------------------------
# TOOL DEFINITIONS
# --------------------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "investigate_incident",
            "description": (
                "Run a complete evidence-based incident investigation. "
                "Returns incident details, potentially affected services, "
                "dependency paths, direct and indirect dependents, linked "
                "runbooks, and an evidence note. Use this first for an "
                "incident investigation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "Incident ID, for example INC-001",
                    }
                },
                "required": ["incident_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_incident_details",
            "description": "Retrieve an incident and its linked service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"}
                },
                "required": ["incident_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_affected_services",
            "description": (
                "Find services that depend on a service. "
                "Results indicate potential impact, not confirmed failure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"}
                },
                "required": ["service_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_runbooks",
            "description": "Retrieve runbooks linked to a service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"}
                },
                "required": ["service_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dependency_chain",
            "description": "Retrieve dependency paths leading to a service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string"}
                },
                "required": ["service_name"],
                "additionalProperties": False,
            },
        },
    },
]


available_functions = {
    "investigate_incident": investigate_incident,
    "get_incident_details": get_incident_details,
    "find_affected_services": find_affected_services,
    "get_runbooks": get_runbooks,
    "get_dependency_chain": get_dependency_chain,
}

registered_tool_names = {
    item["function"]["name"] for item in tools
}


# --------------------------------------------------
# SYSTEM PROMPT
# --------------------------------------------------

SYSTEM_PROMPT = """
You are TraceFix, an evidence-first AI incident investigation agent.

Use only the registered tools and their exact names.

For a request to investigate an incident:
1. Call investigate_incident first with the incident ID.
2. If the result contains an error or says the incident was not found,
   report that clearly. Do not invent data or investigate another incident.
3. Use the returned structured evidence to prepare the report.
4. Do not call individual tools again for the same investigation unless
   the user asks a separate, specific follow-up that requires them.

EVIDENCE RULES:
- Separate recorded facts, potential impact, hypotheses, and recommendations.
- Preserve incident titles and stored runbook steps accurately.
- Label any extra troubleshooting advice as additional recommendations.
- Dependency relationships do not prove that a service has failed.
- An incident title does not establish the current live state.
- Without diagnostic logs, metrics, traces, or test results, the root
  cause remains unconfirmed.
- Do not invent monitoring results, logs, runbooks, or root causes.

DEPENDENCY DIRECTION:
If A-[:DEPENDS_ON]->B, A depends on B.
For path [A, B, C], A depends on B and B depends on C.
B is the direct dependent of C; A is an indirect dependent through B.

In the current graph:
API Gateway -> Payment Service -> Database.
Payment Service directly depends on Database.
API Gateway indirectly depends on Database through Payment Service.
Never claim API Gateway directly depends on Database.

Present concise, clear incident reports grounded in tool results.
"""


# --------------------------------------------------
# AGENT EXECUTION
# --------------------------------------------------

def run_agent(user_question):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]

    max_rounds = 5

    for _ in range(max_rounds):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            parallel_tool_calls=False,
        )

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls

        if not tool_calls:
            return assistant_message.content or "No response generated."

        # Preserve the Groq SDK assistant message object for tool calling.
        messages.append(assistant_message)

        for tool_call in tool_calls:
            name = tool_call.function.name

            try:
                if name not in registered_tool_names:
                    result = {
                        "success": False,
                        "error": (
                            f"Unregistered tool '{name}'. "
                            f"Use only: {sorted(registered_tool_names)}"
                        ),
                    }
                else:
                    arguments = json.loads(
                        tool_call.function.arguments or "{}"
                    )

                    print(f"[TraceFix] Running tool: {name}")

                    data = available_functions[name](**arguments)

                    result = {
                        "success": True,
                        "data": data,
                    }

                    # If the combined investigation cannot find an incident,
                    # instruct the model not to invent a report.
                    if (
                        name == "investigate_incident"
                        and isinstance(data, dict)
                        and data.get("error")
                    ):
                        result["message"] = (
                            "Incident not found. Report this clearly. "
                            "Do not call other investigation tools."
                        )

                    if name == "get_incident_details" and data is None:
                        result["message"] = (
                            "Incident not found. Stop investigation."
                        )

            except Exception as error:
                result = {
                    "success": False,
                    "error": f"{name} failed: {error}",
                }

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                }
            )

    # Ask for a final response if the tool-call limit is reached.
    messages.append(
        {
            "role": "user",
            "content": (
                "Give a final summary using only evidence already retrieved. "
                "Do not request more tools. State missing information."
            ),
        }
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    return (
        response.choices[0].message.content
        or "No final report generated."
    )


# --------------------------------------------------
# TERMINAL INTERFACE
# --------------------------------------------------

if __name__ == "__main__":
    print("TraceFix — AI Incident Investigation")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_question = input("Describe an incident: ").strip()

            if user_question.lower() in {"exit", "quit"}:
                print("TraceFix stopped.")
                break

            if not user_question:
                continue

            answer = run_agent(user_question)
            print("\nTraceFix Report:\n")
            print(answer)
            print("\n" + "-" * 50 + "\n")

        except KeyboardInterrupt:
            print("\nTraceFix stopped.")
            break
        except Exception as error:
            print(f"\nTraceFix error: {error}\n")
