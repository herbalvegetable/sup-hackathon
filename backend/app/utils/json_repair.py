import re
import json


def strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` fences from LLM output."""
    text = text.strip()
    # Remove leading ```json or ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    # Remove trailing ```
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_json_object(text: str) -> str:
    """Extract the first JSON object or array from a string."""
    # Try to find a JSON object
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def safe_parse_json(text: str) -> dict:
    """Attempt to parse JSON, stripping markdown fences first."""
    cleaned = strip_markdown_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try extracting just the JSON portion
        extracted = extract_json_object(cleaned)
        return json.loads(extracted)
