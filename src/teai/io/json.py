import json
from datetime import datetime

from json_repair import repair_json
from litellm.types.utils import ModelResponse

from teai.core.exceptions import LLMResponseError
from teai.events.event import Event
from teai.events.observation import CmdOutputMetadata
from teai.events.serialization import event_to_dict
from teai.llm.metrics import Metrics


class TeAIJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and event objects"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Event):
            return event_to_dict(obj)
        if isinstance(obj, Metrics):
            return obj.get()
        if isinstance(obj, ModelResponse):
            return obj.model_dump()
        if isinstance(obj, CmdOutputMetadata):
            return obj.model_dump()
        return super().default(obj)


# Create a single reusable encoder instance
_json_encoder = TeAIJSONEncoder()


def dumps(obj, **kwargs):
    """Serialize an object to str format"""
    if not kwargs:
        return _json_encoder.encode(obj)
    return json.dumps(obj, cls=TeAIJSONEncoder, **kwargs)


def loads(json_str, **kwargs):
    """Create a JSON object from str"""
    try:
        return json.loads(json_str, **kwargs)
    except json.JSONDecodeError:
        pass
    depth = 0
    start = -1
    for i, char in enumerate(json_str):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start != -1:
                response = json_str[start : i + 1]
                try:
                    json_str = repair_json(response)
                    return json.loads(json_str, **kwargs)
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    raise LLMResponseError(
                        'Invalid JSON in response. Please make sure the response is a valid JSON object.'
                    ) from e
    raise LLMResponseError('No valid JSON object found in response.')
