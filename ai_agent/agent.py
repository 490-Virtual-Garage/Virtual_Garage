import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from .prompt import SYSTEM_PROMPT
from .tools import get_obd_data, get_diagnosis

load_dotenv()

client = OpenAI()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")

TOOLS = [
    {
        "type": "function",
        "name": "get_obd_data",
        "description": "Retrieve the latest OBD-II readings and DTCs.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "get_diagnosis",
        "description": (
            "Retrieve approved diagnostic causes and "
            "recommended tests from the rule engine."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "strict": True
    }
]

TOOL_FUNCTIONS = {
    "get_obd_data": get_obd_data,
    "get_diagnosis": get_diagnosis
}


def ask_mechanic(message):
    conversation = [
        {"role": "user", "content": message}
    ]

    for _ in range(5):

        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=conversation,
            tools=TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False
        )

        conversation.extend(
            item.model_dump(exclude_none=True)
            for item in response.output
        )

        tool_calls = [
            item for item in response.output
            if item.type == "function_call"
        ]

        if not tool_calls:
            return response.output_text

        for call in tool_calls:

            function = TOOL_FUNCTIONS.get(call.name)

            if function is None:
                result = {"error": "Unknown tool"}
            else:
                try:
                    arguments = json.loads(call.arguments)
                    result = function(**arguments)

                except (TypeError, ValueError) as error:
                    result = {
                        "error": "Tool execution failed",
                        "details": str(error)
                    }

            conversation.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json.dumps(result)
            })

    return "Unable to complete the diagnosis."