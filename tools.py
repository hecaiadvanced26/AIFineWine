"""Two tools: execute a SQL query or prepare an order."""
import json
import sqlite3

from catalog import run_query
from orders import prepare_order
from prompts import ATTRIBUTE_DESCRIPTIONS, DATABASE_SCHEMA


def tool(name, description, properties):
    return {"type": "function", "function": {"name": name,
        "description": description, "parameters": {"type": "object",
        "properties": properties, "required": list(properties),
        "additionalProperties": False}}}


TOOLS = [
    tool("run_query", "Execute one read-only SQLite SELECT. Returns up to ten rows.\n"
         + DATABASE_SCHEMA + ATTRIBUTE_DESCRIPTIONS,
         {"sql": {"type": "string", "description": "The complete SELECT query."}}),
    tool("prepare_order", "Prepare a draft for the chosen wine and quantity. "
         "The customer must click Confirm order or type /confirm to export it.",
         {"wine_id": {"type": "string"},
          "quantity": {"type": "integer", "minimum": 1}}),
]
FUNCTIONS = {"run_query": run_query, "prepare_order": prepare_order}


def reject_constant(value):
    raise ValueError(f"Invalid JSON number: {value}")


def dispatch(name, arguments, memory):
    if name not in FUNCTIONS:
        return {"status": "error", "error": "Unknown tool."}
    try:
        args = json.loads(arguments, parse_constant=reject_constant)
        result = FUNCTIONS[name](**args)
    except (ValueError, TypeError) as error:
        return {"status": "invalid_arguments", "error": str(error)[:250]}
    except sqlite3.Error as error:
        return {"status": "query_error", "error": str(error)}
    if name == "prepare_order" and "error" not in result:
        memory.pending_order = result
    return result
