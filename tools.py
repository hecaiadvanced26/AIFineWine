"""Tools: SQL lookup, guided recommendations, cheaper alternatives, quick replies, order draft."""
import json
import sqlite3

from advisor import (FAMILIES, TYPES, find_cheaper_alternatives, offer_choices,
                     recommend_wines)
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
TOOLS += [
    tool("recommend_wines",
         "Rank in-stock wines for a customer profile. Colour and budget are strict filters; aromas "
         "and country only rank. Returns at most 3 wines with the wishes they meet. Use this for "
         "'help me choose' requests instead of writing SQL.",
         {"wine_type": {"type": "string", "enum": list(TYPES)},
          "budget_min_eur": {"type": ["number", "null"]},
          "budget_max_eur": {"type": ["number", "null"]},
          "aroma_families": {"type": "array", "items": {"type": "string", "enum": list(FAMILIES)}},
          "aromas": {"type": "array", "items": {"type": "string"},
                     "description": "Specific aroma tags from the catalog list; usually empty."},
          "country": {"type": ["string", "null"]},
          "include_style_guesses": {"type": "boolean",
                                    "description": "False unless the customer agreed to guessed aromas."}}),
    tool("find_cheaper_alternatives",
         "For one wine ID, find up to 2 cheaper in-stock wines of the same colour that share aroma tags.",
         {"wine_id": {"type": "string"}}),
    tool("offer_choices",
         "Show 2-6 tappable answers under your next question. Use for guided advice questions.",
         {"options": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 6},
          "step": {"type": "integer", "minimum": 1}, "total": {"type": "integer", "minimum": 1}}),
]
FUNCTIONS = {"run_query": run_query, "prepare_order": prepare_order,
             "recommend_wines": recommend_wines, "find_cheaper_alternatives": find_cheaper_alternatives,
             "offer_choices": offer_choices}


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
    elif name == "recommend_wines" and result.get("wines"):
        memory.recommendations = {"wishes": result["wishes"], "wines": result["wines"]}
    elif name == "find_cheaper_alternatives" and result.get("alternatives"):
        memory.comparison = {"chosen": result["chosen"], "alternatives": result["alternatives"]}
    elif name == "offer_choices" and result.get("status") == "shown":
        memory.choices = {key: result[key] for key in ("options", "step", "total")}
    return result
