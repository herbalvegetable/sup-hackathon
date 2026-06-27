import json
from openai import AsyncOpenAI
from app.config import settings

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def call_gpt4o(
    system_prompt: str,
    user_message: str,
    response_format: str = "json_object",
    max_tokens: int = 4096,
) -> str:
    """Call GPT-4o and return the response text."""
    client = get_client()
    
    kwargs = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }
    
    if response_format == "json_object":
        kwargs["response_format"] = {"type": "json_object"}
    
    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


async def call_gpt4o_text(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 512,
) -> str:
    """Call GPT-4o for plain text output (not JSON)."""
    client = get_client()
    
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content or ""
