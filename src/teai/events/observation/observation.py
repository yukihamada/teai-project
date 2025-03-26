from dataclasses import dataclass

from teai.events.event import Event


@dataclass
class Observation(Event):
    content: str
