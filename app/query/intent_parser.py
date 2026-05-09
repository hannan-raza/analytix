import json
import os

from openai import OpenAI

from app.logger import get_logger
from app.query.exceptions import PipelineError

logger = get_logger(__name__)

_SYSTEM_PROMPT = """
You are an analytics intent parser.

Return ONLY valid JSON.

Schema:
{
  "intent": "",
  "entity": "",
  "metrics": [],
  "time_range": "",
  "operation": "",
  "filters": {}
}

Examples:
User: how many products do we have
Output:
{"intent":"count","entity":"products"}

User: how many orders today
Output:
{"intent":"count","entity":"orders","time_range":"today"}

User: how many orders of laptop
Output:
{"intent":"count","entity":"orders","filters":{"product_name":"laptop"}}

User: show me orders for cricket bat
Output:
{"intent":"show","entity":"orders","filters":{"product_name":"cricket bat"}}

User: show me user names and emails
Output:
{"intent":"show","entity":"users","metrics":["name","email"]}
"""


def get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_question(question: str) -> dict:
    logger.info("Parsing question: %r", question)
    raw = ""
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
        )
        raw = response.choices[0].message.content
        intent = json.loads(raw)
        logger.info("Intent: %s", intent)
        return intent
    except json.JSONDecodeError:
        logger.error("GPT returned invalid JSON: %r", raw)
        raise PipelineError(
            "Could not understand the question — please try rephrasing it.",
            stage="intent",
        )
    except Exception as e:
        logger.error("Intent parser failed: %s", e)
        raise PipelineError(
            "Failed to reach the AI service. Please try again.",
            stage="intent",
        )
