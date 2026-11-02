import os
from datetime import datetime, timezone
from typing import Any, cast

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from openai import OpenAIError
from pydantic import SecretStr, BaseModel
from .model_db import SEVERITY_LIST, INTENT_LIST,compute_deadline
from .schema import TicketStruct, TicketCreate


load_dotenv()
API_KEY = SecretStr(os.getenv("OPENAI_API_KEY",""))
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
if API_KEY.get_secret_value() == "":
    raise ValueError("API_KEY not set")


def build_openai():
    return ChatOpenAI(api_key=API_KEY,model=MODEL)

def build_prompt(message: str) ->str:
    return f"""
    You are an AI assistant for an internal customer support system.
    You will receive a feedback message from a customer and analyze its content to create a support ticket.
    Based on the message, classify the ticket by intent, severity, and the product it refers to.
    If the customer does not mention any product, set product to null. If the message is vague or unclear, set intent to "OTHER".
    summary have max length of 200 characters and contain reason for severity

    INTENT LIST
    {", ".join(INTENT_LIST)}

    SEVERITY LIST
    {", ".join(SEVERITY_LIST)}

    CUSTOMER MESSAGE
    {message}
""".strip()

ai_model = build_openai().with_structured_output(TicketCreate)
async def handle_client_message(message: str) -> TicketCreate:
    try :
        res = await ai_model.ainvoke(build_prompt(message))
    except OpenAIError as e:
        print(e)
        raise e
    return cast(TicketCreate,res)

