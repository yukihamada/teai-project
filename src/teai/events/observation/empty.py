from dataclasses import dataclass

from teai.core.schema import ObservationType
from teai.events.observation.observation import Observation


@dataclass
class NullObservation(Observation):
    """This data class represents a null observation.
    This is used when the produced action is NOT executable.
    """

    observation: str = ObservationType.NULL

    @property
    def message(self) -> str:
        return 'No observation'
