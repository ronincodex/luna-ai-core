from abc import ABC, abstractmethod
from typing import Dict, Any


class Tool(ABC):
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool and return a dict with result or error."""
        pass

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """JSON Schema for parameters."""
        pass
