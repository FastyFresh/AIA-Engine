from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

logging.basicConfig(level=logging.INFO)

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def run(self, *args, **kwargs) -> Dict[str, Any]:
        pass
    
    def log(self, message: str, level: str = "info"):
        log_func = getattr(self.logger, level, self.logger.info)
        log_func(f"[{self.name}] {message}")
